
import typing
import numbers

class Inputs(typing.NamedTuple):
    openbutton_outside: bool = False  # True if pressed
    openbutton_inside: bool  = False
    holdopen_button: bool = False
    mqtt_connected: bool  = False
    mqtt_request: typing.Any = None
    current_time: int = 0
    #door_present: bool

# States
class Locked(typing.NamedTuple):
    since: int
class Unlocked(typing.NamedTuple):
    since: int
class TemporarilyUnlocked(typing.NamedTuple):
    since: int
    until: int

class Inactive(typing.NamedTuple):
    since: int
class Active(typing.NamedTuple):
    since: int
class TemporarilyActive(typing.NamedTuple):
    since: int
    until: int    
   
LockState = typing.Union[Unlocked,Locked,TemporarilyUnlocked]
OpenerState = typing.Union[Inactive,Active,TemporarilyActive]

class States(typing.NamedTuple):
    lock: LockState = Locked(0)
    opener: OpenerState = Inactive(0)
    connected_light: bool = False
    #unlocked_light: bool

def next_state(current: States, inputs: Inputs) -> States:
    i = inputs

    # Doorlock
    lock = current.lock
    if i.mqtt_request is not None:
        # number of seconds
        if isinstance(i.mqtt_request, numbers.Number):
            until = i.current_time+i.mqtt_request
            lock = TemporarilyUnlocked(since=i.current_time, until=until)
        # hard on/off
        elif i.mqtt_request == True:
            lock = Unlocked(since=i.current_time)
        elif i.mqtt_request == False:
            lock = Locked(since=i.current_time)
    
    if isinstance(lock, TemporarilyUnlocked) and i.current_time >= lock.until:
        lock = Locked(since=i.current_time)

    # Opener
    opener = current.opener
    open_pressed = i.openbutton_outside or i.openbutton_inside

    # hard on/off
    if isinstance(opener, (Inactive,TemporarilyActive)) and i.holdopen_button == True:
        opener = Active(since=i.current_time)
    elif isinstance(opener, Active) and i.holdopen_button == False:
        opener = Active(since=i.current_time)
    # timed opening
    elif isinstance(opener, (Inactive,TemporarilyActive)) and open_pressed == True:
        opener = TemporarilyActive(since=i.current_time, until=i.current_time+20)     
    elif isinstance(opener, TemporarilyActive) and i.current_time >= opener.until:
        opener = Inactive(since=i.current_time)

    state = States(
        connected_light=i.mqtt_connected,
        lock=lock,
        opener=opener, 
    )

    return state 


if __name__ == '__main__':
    i = Inputs(
        openbutton_outside=True,
        openbutton_inside=False,
        mqtt_connected=True,
        mqtt_request=True,
        holdopen_button=False,
        current_time=100,
    )
    s = States()
    print(s)
    s = next_state(s, i)
    print(s)
    m = i._asdict()
    m['current_time'] = 130
    m['openbutton_outside'] = False
    m['mqtt_request'] = 30 
    i = Inputs(**m)
    s = next_state(s, i)
    print(s)
    m['current_time'] = 200
    m['mqtt_request'] = None
    s = next_state(s, Inputs(**m))
    print(s)


