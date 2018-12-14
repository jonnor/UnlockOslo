

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
import math
import copy

import logging
logging.basicConfig()
log_level = os.environ.get('LOGLEVEL', 'info')
level = getattr(logging, log_level.upper())
log = logging.getLogger('firmware')
log.setLevel(level)

class Inputs():
    def __init__(self,
        openbutton_outside : bool = False,
        openbutton_inside : bool = False,
        holdopen_button : bool = False,
        door_present : bool = False,
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
        until : float = None,
        reason : str = None,
        ) -> None:
        
        self.state = state
        self.since = since
        self.until = until
        self.reason = reason

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
        action, data = i.mqtt_request
        # unlock permanently
        if action == 'unlock' and isinstance(data, bool) and data == True:
            lock = Unlocked(since=i.current_time)
        # unlock for number of seconds
        elif action == 'unlock' and isinstance(data, int):
            until = i.current_time + data
            lock = TemporarilyUnlocked(since=i.current_time, until=until)
        # lock permanently
        elif action == 'lock' and isinstance(data, bool) and data == True:
            lock = Locked(since=i.current_time)
        else:
            raise ValueError('Invalid MQTT request data: {}'.format(data))

    if lock.state == 'TemporarilyUnlocked' and i.current_time >= lock.until:
        lock = Locked(since=i.current_time)

    # Opener
    opener = current.opener
    opener_time = 10

    def ensure_unlocked_for_opener():
        assert opener.state in ('Active', 'TemporarilyActive')
        temp_unlock_time = 5
        nonlocal lock
        if lock.state in ('Locked', 'TemporarilyUnlocked'):
            lock = TemporarilyUnlocked(since=i.current_time, until=i.current_time+temp_unlock_time)

    # unlock switch
    if i.holdopen_button == True:
        lock = Unlocked(since=i.current_time, reason='switch')
    elif i.holdopen_button == False and lock.state == 'Unlocked' and lock.reason == 'switch':
        lock = Locked(since=i.current_time, reason='switch') 

    # inside button
    if opener.state in ('Inactive','TemporarilyActive') and i.openbutton_inside == True:
        opener = TemporarilyActive(since=i.current_time, until=i.current_time+opener_time)
        ensure_unlocked_for_opener()

    # outside button
    elif opener.state in ('Inactive','TemporarilyActive') and i.openbutton_outside == True:
        if lock.state in ('Unlocked', 'TemporarilyUnlocked'):
            opener = TemporarilyActive(since=i.current_time, until=i.current_time+opener_time)
        else:
            # DENY. user is outside, door is locked, have to unlock using app first
            pass

    # shut off again
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
            with open(path, 'w') as f:
                f.write('0')

        files = input_files if direction == 'in' else output_files
        files[name] = path

    return input_files, output_files

def set_gpio(file_path : str, on : bool):
    s = "1" if on else "0"
    with open(file_path, 'w') as f:
        f.write(s)

def set_outputs(states : States, file_paths):
    s = {
        'opener': states.opener.state != 'Inactive',
        'lock': states.lock.state == 'Locked', # solenoid is locked when active
        'connected_light': states.connected_light,
        'door_unlocked_light': states.lock.state != 'Locked',
    }
    for name, on in s.items():
        set_gpio(file_paths[name], on)


# Board input/output to GPIO pin mapping
ins = {
    1: 25,
    2: 10,
    3: 24,
    4: 22,
    5: 23,
    6: 27,
    7: 18,
    8: 17,
}
outs = {
    1: 6,
    2: 19,
    3: 16,
    4: 26,
    5: 20,
    6: 21,
}
status = {
    1: 12,
    2: 13,
}

participant_definition = {
  'component': 'dlock-oslo/Door',
  'label': 'A door that can be locked and unlocked',
  'icon': 'clock-o',
  'inports': [
    { 'id': 'unlock', 'type': 'number' },
    { 'id': 'lock', 'type': 'bool' },
  ],
  'outports': [
    { 'id': 'error', 'type': 'string' },
    { 'id': 'islocked', 'type': 'bool' },
    { 'id': 'openeractive', 'type': 'bool' },
    { 'id': 'doorpresent', 'type': 'bool' },
  ],
}

# Used for testing
class AlwaysErroringParticipant(msgflo.Participant):
  def __init__(self, role):
    d = copy.deepcopy(participant_definition)
    msgflo.Participant.__init__(self, d, role)

  def process(self, inport, msg):
    if inport == 'lock':
        self.send('error', "Lock request fails always")
    elif inport == 'unlock':
        self.send('error', "Unlock request fails always")
    else:
        self.send('error', 'Unknown port {}'.format(inport))
    self.ack(msg)

class LockParticipant(msgflo.Participant):
  def __init__(self, role):
    d = copy.deepcopy(participant_definition)
    msgflo.Participant.__init__(self, d, role)

    self.discovery_period = float(os.environ.get("DLOCK_DISCOVERY_PERIOD", "60"))

    pin_mapping = {
        # in
        'holdopen_button': ('in', ins[1]),
        'openbutton_outside': ('in', ins[2]),
        'openbutton_inside': ('in', ins[3]),
        'door_present': ('in', ins[4]),
        # out
        'lock': ('out', outs[1]),
        'opener': ('out', outs[2]),
        'connected_light': ('out', outs[3]),
        'door_unlocked_light': ('out', outs[4]),
    }

    # Take input from plain files, mostly useful for testing on non-Raspberry deives
    fake_gpio = os.environ.get('DLOCK_FAKE_GPIO')
    if fake_gpio:
        if not os.path.exists(fake_gpio):
            os.mkdir(fake_gpio)
        pin_mapping = { p: (cfg[0], '{}/gpio{}'.format(fake_gpio, cfg[1])) for p, cfg in pin_mapping.items() }

    i, o = setup_gpio(pin_mapping)
    self.input_files = i
    self.output_files = o

    self.state = States(
        lock = Locked(0),
        opener = Inactive(0),
        connected_light = False,
    )
    self.inputs = Inputs()

    gevent.Greenlet.spawn(self.loop)

  def process(self, inport, msg):
    if inport == 'unlock':
        self.recalculate_state((inport, msg.data))
    elif inport == 'lock':
        self.recalculate_state((inport, msg.data))
    else:
        pass
    self.ack(msg)

  def loop(self):
    while True:
        self.recalculate_state()
        gevent.sleep(0.2)

  def recalculate_state(self, mqtt_request=None):
    # Retrieve current inputs
    connected = getattr(self, '_engine', None) and self._engine.connected

    if connected:
        self._engine.discovery_period = self.discovery_period

    inputs = dict(
        current_time=math.ceil(time.monotonic()),
        mqtt_request=mqtt_request,
        mqtt_connected=connected,
    )
    gpio_inputs = { i: read_boolean(p) for i, p in self.input_files.items() }
    gpio_inputs['openbutton_outside'] = not gpio_inputs['openbutton_outside']   # active-low
    gpio_inputs['openbutton_inside'] = not gpio_inputs['openbutton_inside']   # active-low
    inputs.update(gpio_inputs)
    next = next_state(self.state, Inputs(**inputs))
    set_outputs(self.state, self.output_files)

    state_changed = next.__dict__ != self.state.__dict__
    if state_changed:
        entry = { 'inputs': inputs, 'state': next.__dict__ }
        log.info(entry)

        if connected:
            self.send('islocked', next.lock.state == 'Locked')
            self.send('openeractive', next.opener.state != 'Inactive')
            self.send('doorpresent', inputs['door_present'])

    self.state = next
    self.inputs = inputs

def main():
    role = os.environ.get('DLOCK_ROLE')
    if len(sys.argv) >= 2:
        role = sys.argv[1]
    p = msgflo.main(LockParticipant, role=role)

if __name__ == '__main__':
    main()
