"""Test door system logic"""

import dlockoslo

import pytest

def test_compound():
    states = dlockoslo.States()
    assert isinstance(states.lock, dlockoslo.Locked)

    inputs = dict(
        openbutton_outside=False,
        openbutton_inside=False,
        mqtt_connected=True,
        mqtt_request=False,
        holdopen_button=False,
        current_time=100,
    )

    # unlock, trigger dooropener
    inputs['openbutton_outside'] = True
    inputs['mqtt_request'] = ('unlock', True)
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs)) 
    assert states.connected_light == True
    assert states.lock.state == 'Unlocked'
    assert states.opener.state == 'TemporarilyActive'

    # forward until dooropened deactived, trigger time-based door unlocking
    inputs['current_time'] = 130
    inputs['openbutton_outside'] = False
    inputs['mqtt_request'] = ('unlock', 30) 
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.opener.state == 'Inactive'
    assert states.lock.state == 'TemporarilyUnlocked'

    # clear MQTT message, forward time
    inputs['current_time'] = 200
    inputs['mqtt_request'] = None

    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.opener.state == 'Inactive'
    assert states.lock.state == 'Locked'

def test_mqtt_unlock():
    states = dlockoslo.States()
    inputs = dict(
        mqtt_request=('unlock', True),
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.lock.state == 'Unlocked'

def test_mqtt_unlock_duration():
    states = dlockoslo.States()
    inputs = dict(
        current_time=103,
        mqtt_request=('unlock', 11),
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.lock.state == 'TemporarilyUnlocked'
    assert states.lock.until == 103+11

def test_mqtt_lock():
    states = dlockoslo.States(lock=dlockoslo.Unlocked(since=1))
    inputs = dict(
        mqtt_request=('lock', True),
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.lock.state == 'Locked'

def test_mqtt_unlock_when_unlocked():
    states = dlockoslo.States(lock=dlockoslo.Unlocked(since=1))
    inputs = dict(
        mqtt_request=('unlock', True),
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    # should not change state
    assert states.lock.state == 'Unlocked'

def test_mqtt_unlock_duration_when_unlocked():
    states = dlockoslo.States(lock=dlockoslo.Unlocked(since=1))
    inputs = dict(
        mqtt_request=('unlock', True),
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    # should not change state
    assert states.lock.state == 'Unlocked'


def test_openbutton_inside_when_unlocked():
    states = dlockoslo.States(lock=dlockoslo.Unlocked(since=1))
    assert states.lock.state == 'Unlocked'
    inputs = dict(
        openbutton_inside=True,
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    # should just open, leave lock alone
    assert states.lock.state == 'Unlocked'
    assert states.opener.state == 'TemporarilyActive'


def test_openbutton_inside_when_locked():
    states = dlockoslo.States()
    assert states.lock.state == 'Locked'
    inputs = dict(
        openbutton_inside=True,
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    # should unlock and open
    assert states.lock.state == 'TemporarilyUnlocked'
    assert states.opener.state == 'TemporarilyActive'

def test_openbutton_outside_when_locked():
    states = dlockoslo.States()
    assert states.lock.state == 'Locked'
    inputs = dict(
        openbutton_outside=True,
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    # should _not unlock or open_ (user must open door using app first)
    assert states.lock.state == 'Locked'
    assert states.opener.state == 'Inactive'

def test_openbutton_outside_when_unlocked():
    states = dlockoslo.States(lock=dlockoslo.Unlocked(since=1))
    assert states.lock.state == 'Unlocked'
    inputs = dict(
        openbutton_outside=True,
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    # should _not unlock or open_ (user must open door using app first)
    assert states.lock.state == 'Unlocked'
    assert states.opener.state == 'TemporarilyActive'

def test_switch_unlocks_door():
    states = dlockoslo.States()
    assert states.lock.state == 'Locked'
    assert states.opener.state == 'Inactive'
    inputs = dict(
        holdopen_button=True,
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.lock.state == 'Unlocked', 'unlocks'
    assert states.opener.state == 'Inactive', 'leave opener unchanged'

    inputs = dict(
        holdopen_button=False,
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.lock.state == 'Locked'

def test_dooropener_after_unlock():
    states = dlockoslo.States()
    assert states.lock.state == 'Locked'
    assert states.opener.state == 'Inactive'
    inputs = dict(
        holdopen_button=True,
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.lock.state == 'Unlocked', 'unlocks'
    assert states.opener.state == 'Inactive', 'leave opener unchanged'

    inputs = dict(
        holdopen_button=True,
        openbutton_outside=True,
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.opener.state == 'TemporarilyActive'

