
import typing
import numbers

import gevent
import os
import time
import os.path

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
        elif isinstance(data, int):
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

def gpio_file_path(number: int):
    return '/sys/class/gpio/gpio{}/value'.format(number)

# idempotent
def setup_gpio_pin(number : int, direction):
    export_path = '/sys/class/gpio/export'
    direction_path = '/sys/class/gpio{}/direction'.format(number)

    # Export GPIO
    if not os.path.exists(direction_path):
        with open(export_path, 'r') as exportfile:
            exportfile.write(str(number))
        # wait for export done, otherwise direction change fails EACCESS
        time.sleep(10)
    
    # Set direction
    with open(direction_path, 'w') as directionfile:
        directionfile.write(direction)

    # TODO: configure drive current?

def read_boolean(file_path):
    with open(file_path) as f:
        s = f.read()
        return s == '1'

def get_inputs(input_files) -> Inputs:
    gpio_inputs = { i: read_boolean(p) for i, p in input_files.items() }

    b = dict(
        current_time=time.monotonic()
    )
    i = dict()
    i.update(gpio_inputs)
    i.update(b) 

    return Inputs(**i)


def setup_gpio(pinmap):
    input_files = {}
    output_files = {}

    for name, pinconfig in pinmap.items():
        print(pinconfig)

        direction, gpio = pinconfig
        if isinstance(gpio, int):
            setup_gpio_pin(gpio, direction)
            path = gpio_file_path(gpio)
        else:
            # assumed to be a regular file that can be read/written to
            path = gpio

        files = input_files if direction == 'input' else output_files
        files[path] = path

    return input_files, output_files

def main():
    pin_mapping = {
        # in
        'holdopen_button': ('input', 10),
        'openbutton_outside': ('input', 11),
        'openbutton_inside': ('input', 12),
        # out
        'lock': ('output', 13),
        'opener': ('output', 14),
        'connected_light': ('output', 15),
    }

    # TEMP: testing using plain-files
    pin_mapping = { p: (cfg[0], 'gpio{}'.format(cfg[1])) for p, cfg in pin_mapping.items() } 

    input_files, output_files = setup_gpio(pin_mapping)

    state = States()
    while True:
        i = get_inputs(input_files)
        state = next_state(state, i)        
        print(i, state)
        time.sleep(0.2)

if __name__ == '__main__':
    main()
