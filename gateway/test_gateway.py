
import gateway
import testdevices

import flask
import pytest
import gevent
import json
import base64

import os

app = gateway.app
gateway.api_users['TEST_USER'] = 'XXX_TEST_PASSWORD'

def basic_auth(u, p):
    s = "{}:{}".format(u, p)
    n = base64.b64encode(s.encode('utf8'))
    return b"Basic " + n

def authed(**kwargs):
    username = kwargs.get('username', 'TEST_USER')
    password = kwargs.get('password', 'XXX_TEST_PASSWORD')
    if kwargs.get('username') is not None:
        del kwargs['username']
    if kwargs.get('password') is not None:
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
def test_missing_credentials_401(devices):
    with app.test_client() as c:
        r = c.post("doors/virtual-1/unlock?timeout=1.0")
        body = r.data.decode('utf8')
        assert r.status_code == 401

def test_wrong_password_403(devices):
    with app.test_client() as c:
        r = c.post("doors/virtual-1/unlock?timeout=1.0", **authed(password='wrong'))
        body = r.data.decode('utf8')
        assert r.status_code == 403

def test_empty_password_403(devices):
    with app.test_client() as c:
        r = c.post("doors/virtual-1/unlock?timeout=1.0", **authed(password=''))
        body = r.data.decode('utf8')
        assert r.status_code == 403

def test_invalid_user_403(devices):
    with app.test_client() as c:
        r = c.post("doors/virtual-1/unlock?timeout=1.0", **authed(username='invalid'))
        body = r.data.decode('utf8')
        assert r.status_code == 403

def test_invalid_user_emptypass_403(devices):
    with app.test_client() as c:
        r = c.post("doors/virtual-1/unlock?timeout=1.0", **authed(username='invalid', password=''))
        body = r.data.decode('utf8')
        assert r.status_code == 403

def test_wrong_ip_403(devices):
    with app.test_client() as c:
        u = "doors/virtual-1/unlock?timeout=1.0"
        shouldwork = c.post(u, **authed())
        assert shouldwork.status_code == 200

        previous_setting = gateway.allowed_ips
        gateway.allowed_ips = ['6.6.6.6']
        shouldfail = c.post(u, **authed())
        gateway.allowed_ips = previous_setting

        body = shouldfail.data.decode('utf8')
        assert shouldfail.status_code == 403
        assert 'Access denied' in body

@pytest.fixture(scope="module")
def devices():
    gateway.mqtt_client = gateway.setup_mqtt_client()
    gevent.sleep(1) # ensure we are connected/subcribed before discovery
    testdevices.run()
    gevent.sleep(1) # let the devices spin up


# POST /door/id/unlock
def test_unlock_successful(devices):
    with app.test_client() as c:
        r = c.post("doors/virtual-1/unlock?timeout=1.0", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 200
        assert 'unlocked' in body

def test_unlock_errors(devices):
    with app.test_client() as c:
        r = c.post("doors/erroring-1/unlock", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 502
        assert 'error' in body
        assert 'fails always' in body

def test_unlock_timeout(devices):
    with app.test_client() as c:
        r = c.post("doors/notresponding-1/unlock?timeout=0.5", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 504

def test_unlock_with_duration(devices):
    with app.test_client() as c:
        r = c.post("doors/virtual-1/unlock?duration=1", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 200
        gevent.sleep(2) # ensure is locked again at end of test


# POST /door/id/lock
def test_lock_successful(devices):
    with app.test_client() as c:
        r = c.post("doors/virtual-1/lock", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 200
        assert ' locked' in body

def test_lock_timeout(devices):
    with app.test_client() as c:
        r = c.post("doors/notresponding-1/lock?timeout=0.5", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 504

def test_lock_errors(devices):
    with app.test_client() as c:
        r = c.post("doors/erroring-1/lock", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 502
        assert 'error' in body
        assert 'fails always' in body

# GET /status
def test_status_missing_device_503(devices):
    with app.test_client() as c:
        r = c.get("status")
        body = r.data.decode('utf8')
        assert r.status_code == 503
        assert r.content_type == 'application/json'
        details = json.loads(body)
        assert details['doors']['sorenga-1']['status'] == 503
        assert details['doors']['virtual-1']['status'] == 200
        assert details['doors']['virtual-1']['last_seen'] >= 1512050000

def test_status_all_devices_ok(devices):
    with app.test_client() as c:
        r = c.get("status?ignore=sorenga-1&ignore=notresponding-1")
        body = r.data.decode('utf8')
        assert r.content_type == 'application/json'
        assert r.status_code == 200, body
        details = json.loads(body)
        statuses = [ d['status'] for d in details['doors'].values() ]
        assert statuses == [200] * len(statuses)
        assert 'sorenga-2' not in details['doors'].keys()

def test_status_seen_but_too_long_ago(devices):
    with app.test_client() as c:
        r = c.get("status?ignore=sorenga-1&ignore=notresponding-1&timeperiod=1")
        body = r.data.decode('utf8')
        assert r.status_code == 503, body
        details = json.loads(body)
        assert details['doors']['virtual-1']['status'] == 503

