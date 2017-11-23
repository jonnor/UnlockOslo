
import gateway
import testdevices

import flask
import pytest
import gevent
import json
import base64

app = gateway.app
gateway.api_users['TEST_USER'] = 'XXX_TEST_PASSWORD'

def basic_auth(u, p):
    s = "{}:{}".format(u, p)
    n = base64.b64encode(s.encode('utf8'))
    return b"Basic " + n

def authed(**kwargs):
    username = kwargs.get('username', 'TEST_USER')
    password = kwargs.get('password', 'XXX_TEST_PASSWORD')
    if kwargs.get('username'):
        del kwargs['username']
    if kwargs.get('password'):
        del kwargs['password']
    headers = kwargs.get('headers', {})
    headers['Authorization'] = basic_auth(username, password)
    kwargs['headers'] = headers
    return kwargs

@pytest.mark.parametrize("verb,action", [
    ("GET", "/state"),
    ("POST", "/unlock"),
    ("POST", "/lock"),
])
def test_unknown_door_404(verb, action):
    doorid = "unknown-door-id-666"
    with app.test_client() as client:
        r = getattr(client, verb.lower())("doors/{}{}".format(doorid, action), **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 404
        assert 'Unknown' in body
        assert 'unknown-door-id-666' in body


# TODO: parametrize
def test_missing_credentials_401():
    with app.test_client() as c:
        r = c.post("doors/virtual-1/unlock?timeout=1.0")
        body = r.data.decode('utf8')
        assert r.status_code == 401

def test_wrong_password_403():
    with app.test_client() as c:
        r = c.post("doors/virtual-1/unlock?timeout=1.0", **authed(password='wrong'))
        body = r.data.decode('utf8')
        assert r.status_code == 403


@pytest.fixture(scope="module")
def devices():
    gateway.mqtt_client = gateway.create_client()
    testdevices.run()
    gevent.sleep(1) # let the devices spin up


# POST /door/id/unlock
def test_unlock_successful(devices):
    with app.test_client() as c:
        r = c.post("doors/virtual-1/unlock?timeout=1.0", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 200

def test_unlock_errors(devices):
    with app.test_client() as c:
        r = c.post("doors/erroring-1/unlock", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 502

def test_unlock_timeout(devices):
    with app.test_client() as c:
        r = c.post("doors/notresponding-1/unlock?timeout=0.5", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 504

def test_unlock_with_duration(devices):
    with app.test_client() as c:
        r = c.post("doors/virtual-1/unlock?duration=5", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 200


# POST /door/id/lock
@pytest.mark.skip()
def test_lock_successful(devices):
    with app.test_client() as c:
        r = c.post("doors/notresponding-1/lock?timeout=0.5", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 504


# GET /status
def test_status_missing_device_503(devices):
    with app.test_client() as c:
        r = c.get("status")
        body = r.data.decode('utf8')
        assert r.status_code == 503
        assert 'Missing' in body
        assert 'sorenga-1' in body # not in testdevice set
        assert not 'virtual-1' in body

def test_status_all_devices_ok(devices):
    with app.test_client() as c:
        r = c.get("status?ignore=sorenga-1&ignore=notresponding-1")
        body = r.data.decode('utf8')
        assert r.status_code == 200, body

def test_status_seen_but_too_long_ago(devices):
    with app.test_client() as c:
        r = c.get("status?ignore=sorenga-1&ignore=notresponding-1&timeperiod=1")
        body = r.data.decode('utf8')
        assert r.status_code == 503, body

