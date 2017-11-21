
import gateway

import flask
import pytest
import requests
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


def test_unlock_successful():
    with app.test_client() as c:
        doorid = "virtual-1"
        r = c.post("doors/{}/unlock".format(doorid))
        body = r.data.decode('utf8')
        assert r.status_code == 200

@pytest.mark.skip()
def test_unlock_errored():
    pass

@pytest.mark.skip()
def test_unlock_timeout():
    pass

