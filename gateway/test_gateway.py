
import gateway

import flask
import pytest
import requests
import json

app = gateway.app

def test_unknown_door_404():
    with app.test_client() as c:
        r = c.post("doors/{}/unlock".format("unknown-door-id-666"))
        assert r.status_code == 404
        body = r.data.decode('utf8')
        assert 'Unknown' in body
        assert 'unknown-door-id-666' in body

@pytest.mark.skip()
def test_missing_credentials_403():
    pass

@pytest.mark.skip()
def test_wrong_credentials_403():
    pass

