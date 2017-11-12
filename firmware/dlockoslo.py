
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
        data = i.mqtt_request
        if isinstance(data, bool) and data == True:
            lock = Unlocked(since=i.current_time)
        elif isinstance(data, bool) and data == False:
            lock = Locked(since=i.current_time)
        # number of seconds
        elif isinstance(data, numbers.Number):
            until = i.current_time + data
            lock = TemporarilyUnlocked(since=i.current_time, until=until)
        else:
            raise ValueError('Invalid MQTT request data: {}'.format(data))
    
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


