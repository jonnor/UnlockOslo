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


def test_holdopen_since_updates():
    states = dlockoslo.States()
    assert states.lock.state == 'Locked'
    assert states.opener.state == 'Inactive'
    inputs = dict(
        holdopen_button=True,
        current_time=100,
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.lock.state == 'Unlocked', 'unlocks'
    assert states.lock.since == 100, 'update since on initial transition'

    inputs = dict(
        holdopen_button=True,
        current_time=222,
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.lock.state == 'Unlocked', 'still unlocked'
    assert states.lock.since == 100, 'dont update since when no state transition'


def test_bolt_present_reflects_input():
    states = dlockoslo.States()
    assert states.lock.state == 'Locked'
    assert states.opener.state == 'Inactive'
    inputs = dict(
        bolt_present=False,
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.lock.state == 'Locked'
    assert not states.bolt_present

    # False -> True
    inputs = dict(
        bolt_present=True,
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.lock.state == 'Locked'
    assert states.bolt_present

    # True -> False
    inputs = dict(
        bolt_present=False,
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.lock.state == 'Locked'
    assert not states.bolt_present


@pytest.mark.parametrize('bolt_present', [True, False])
def test_bolt_present_periodic_update(bolt_present):

    states = dlockoslo.States()
    inputs = dict(
        bolt_present=bolt_present,
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.lock.state == 'Locked'
    assert states.bolt_present == bolt_present
    last_updated = states.bolt_present_updated

    inputs = dict(
        bolt_present=bolt_present,
        current_time=30.0, # shorter than update setting
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.lock.state == 'Locked'
    assert states.bolt_present == bolt_present
    assert states.bolt_present_updated == last_updated, 'should not update'

    inputs = dict(
        bolt_present=bolt_present,
        current_time=90.0, # longer than update setting
    )
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert states.lock.state == 'Locked'
    assert states.bolt_present == bolt_present
    assert states.bolt_present_updated > last_updated, 'should update'
    assert states.bolt_present_updated == 90.0

def test_state_change_identity():
    states = dlockoslo.States()
    change = dlockoslo.is_state_change(states, states)
    assert change == False

def test_state_change_equivalence():
    state1 = dlockoslo.States()
    state2 = dlockoslo.States()
    change = dlockoslo.is_state_change(state1, state2)
    assert change == False


def test_state_change_unlocking():
    state1 = dlockoslo.States()
    state1.lock = dlockoslo.Locked(since=10)
    state2 = dlockoslo.States()
    state2.lock = dlockoslo.Unlocked(since=20)

    change = dlockoslo.is_state_change(state1, state2)
    assert change == True, 'unlocking is state change'


