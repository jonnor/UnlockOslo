"""Test door system logic"""

import dlockoslo

def test_simple():
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
    inputs['mqtt_request'] = True
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs)) 
    assert states.connected_light == True
    assert isinstance(states.lock, dlockoslo.Unlocked)
    assert isinstance(states.opener, dlockoslo.TemporarilyActive)

    # forward until dooropened deactived, trigger time-based door unlocking
    inputs['current_time'] = 130
    inputs['openbutton_outside'] = False
    inputs['mqtt_request'] = 30 
    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert isinstance(states.opener, dlockoslo.Inactive)
    assert isinstance(states.lock, dlockoslo.TemporarilyUnlocked)

    # clear MQTT message, forward time
    inputs['current_time'] = 200
    inputs['mqtt_request'] = None

    states = dlockoslo.next_state(states, dlockoslo.Inputs(**inputs))
    assert isinstance(states.opener, dlockoslo.Inactive)
    assert isinstance(states.lock, dlockoslo.Locked)

