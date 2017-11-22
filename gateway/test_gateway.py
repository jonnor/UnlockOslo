
import gateway
import testdevices

import flask
import pytest
import json

app = gateway.app

@pytest.mark.parametrize("verb,action", [
    ("GET", "/state"),
    ("POST", "/unlock"),
    ("POST", "/lock"),
])
def test_unknown_door_404(verb, action):
    doorid = "unknown-door-id-666"
    with app.test_client() as client:
        r = getattr(client, verb.lower())("doors/{}{}".format(doorid, action))
        body = r.data.decode('utf8')
        assert r.status_code == 404
        assert 'Unknown' in body
        assert 'unknown-door-id-666' in body


@pytest.mark.skip()
def test_missing_credentials_403():
    pass

@pytest.mark.skip()
def test_wrong_credentials_403():
    pass


@pytest.fixture(scope="module")
def devices():
    testdevices.run()

def test_unlock_successful(devices):
    with app.test_client() as c:
        r = c.post("doors/virtual-1/unlock")
        body = r.data.decode('utf8')
        assert r.status_code == 200

def test_unlock_errors(devices):
    with app.test_client() as c:
        r = c.post("doors/erroring-1/unlock")
        body = r.data.decode('utf8')
        assert r.status_code == 502

def test_unlock_timeout(devices):
    with app.test_client() as c:
        r = c.post("doors/notresponding-1/unlock")
        body = r.data.decode('utf8')
        assert r.status_code == 504

