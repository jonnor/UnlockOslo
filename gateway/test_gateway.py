
import gateway

import flask
import pytest

@pytest.mark.skip()
def test_door_state_unknown():
    app = gateway.app

    with app.test_request_context():
        u = flask.url_for('door_state', doorid='dør1')
        assert u == 'fail'

@pytest.mark.skip()
def test_unknown_door_404():
    pass

@pytest.mark.skip()
def test_missing_credentials_403():
    pass

@pytest.mark.skip()
def test_wrong_credentials_403():
    pass

