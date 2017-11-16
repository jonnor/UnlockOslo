

import gevent.monkey
gevent.monkey.patch_all()

import gevent
import msgflo

import typing
import numbers
import os
import sys
import time
import os.path
import json

class Inputs():
    def __init__(self,
        openbutton_outside : bool = False,
        openbutton_inside : bool = False,
        holdopen_button : bool = False,
        mqtt_connected : bool = False,
        mqtt_request : typing.Any = None,
        current_time : float = 0) -> None:

        self.openbutton_outside = openbutton_outside
        self.openbutton_inside = openbutton_inside
        self.holdopen_button = holdopen_button
        self.mqtt_connected = mqtt_connected
        self.mqtt_request = mqtt_request
        self.current_time = current_time


# States
class TemporaryBoolean():
    def __init__(self,
        state : str,
        since : float,
        until : float = None) -> None:
        
        self.state = state
        self.since = since
        self.until = until

    def __repr__(self):
        return json.dumps(self.__dict__)

## XXX: nasty
class Inactive(TemporaryBoolean):
    def __init__(self, *args, **kwargs):
        super().__init__('Inactive', *args, **kwargs)
class Active(TemporaryBoolean):
    def __init__(self, *args, **kwargs):
        super().__init__('Active', *args, **kwargs)
class TemporarilyActive(TemporaryBoolean):
    def __init__(self, *args, **kwargs):
        super().__init__('TemporarilyActive', *args, **kwargs)

class Unlocked(TemporaryBoolean):
    def __init__(self, *args, **kwargs):
        super().__init__('Unlocked', *args, **kwargs)
class Locked(TemporaryBoolean):
    def __init__(self, *args, **kwargs):
        super().__init__('Locked', *args, **kwargs)
class TemporarilyUnlocked(TemporaryBoolean):
    def __init__(self, *args, **kwargs):
        super().__init__('TemporarilyUnlocked', *args, **kwargs)

Opener = typing.Union[Inactive,Active,TemporarilyActive]
Lock = typing.Union[Unlocked,Locked,TemporarilyUnlocked]

class States:
    def __init__(self,
        lock : Lock = Locked(0),
        opener : Opener = Inactive(0),
        connected_light : bool = False) -> None:

        self.lock = lock
        self.opener = opener
        self.connected_light = connected_light


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
    
    if lock.state == 'TemporarilyUnlocked' and i.current_time >= lock.until:
        lock = Locked(since=i.current_time)

    # Opener
    opener = current.opener
    open_pressed = i.openbutton_outside or i.openbutton_inside

    # hard on/off
    if opener.state in ('Inactive','TemporarilyActive') and i.holdopen_button == True:
        opener = Active(since=i.current_time)
    elif opener.state == 'Active' and i.holdopen_button == False:
        opener = Inactive(since=i.current_time)
    # timed opening
    elif opener.state in ('Inactive','TemporarilyActive') and open_pressed == True:
        opener = TemporarilyActive(since=i.current_time, until=i.current_time+20)     
    elif opener.state == 'TemporarilyActive' and i.current_time >= opener.until:
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
    direction_path = '/sys/class/gpio/gpio{}/direction'.format(number)

    # Export GPIO
    if not os.path.exists(direction_path):
        with open(export_path, 'w') as exportfile:
            exportfile.write(str(number))
        # wait for export done, otherwise direction change fails EACCESS
        time.sleep(0.1)
    
    # Set direction
    with open(direction_path, 'w') as directionfile:
        directionfile.write(direction)

    # TODO: configure drive current?

def read_boolean(file_path):
    with open(file_path) as f:
        s = f.read().strip() 
        return s == '1'

def setup_gpio(pinmap):
    input_files = {}
    output_files = {}

    for name, pinconfig in pinmap.items():

        direction, gpio = pinconfig
        if isinstance(gpio, int):
            setup_gpio_pin(gpio, direction)
            path = gpio_file_path(gpio)
        else:
            # assumed to be a regular file that can be read/written to
            path = gpio

        files = input_files if direction == 'in' else output_files
        files[name] = path

    return input_files, output_files

class LockParticipant(msgflo.Participant):
  def __init__(self, role):
    d = {
      'component': 'dlock-oslo/DoorLock',
      'label': '',
      'icon': 'clock-o',
      'inports': [
        { 'id': 'unlock', 'type': 'number' },
        { 'id': 'lock', 'type': 'number' },
      ],
      'outports': [
        { 'id': 'state', 'type': 'string' },
      ],
    }

    msgflo.Participant.__init__(self, d, role)

    pin_mapping = {
        # in
        'holdopen_button': ('in', 10),
        'openbutton_outside': ('in', 11),
        'openbutton_inside': ('in', 12),
        # out
        'lock': ('out', 13),
        'opener': ('out', 14),
        'connected_light': ('out', 15),
    }

    # Take input from plain files, mostly useful for testing on non-Raspberry deives
    fake_gpio = os.environ.get('DLOCK_FAKE_GPIO')
    if fake_gpio:
        pin_mapping = { p: (cfg[0], 'gpio{}'.format(cfg[1])) for p, cfg in pin_mapping.items() }

    i, o = setup_gpio(pin_mapping)
    self.input_files = i
    self.output_files = o

    self.state = States(
        lock = Locked(0),
        opener = Inactive(0),
        connected_light = False,
    )

    self.connected = False
    gevent.Greenlet.spawn(self.loop)

  def process(self, inport, msg):
    if inport == 'unlock':
        self.recalculate_state(msg.data)
    elif inport == 'lock':
        pass
    else:
        pass
    self.ack(msg)

  def loop(self):
    while True:
        self.recalculate_state()
        gevent.sleep(0.2)

  def recalculate_state(self, mqtt_request=None):
    # Retrieve current inputs
    inputs = dict(
        current_time=time.monotonic(),
        mqtt_request=mqtt_request,
        mqtt_connected=self.connected,
    )
    gpio_inputs = { i: read_boolean(p) for i, p in self.input_files.items() }
    inputs.update(gpio_inputs)
    next = next_state(self.state, Inputs(**inputs))
    print(inputs)
    print(next.__dict__)
    self.state = next

def main():
    role = sys.argv[1]
    p = msgflo.main(LockParticipant, role=role)

if __name__ == '__main__':
    main()
