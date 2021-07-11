
import gateway
import testdevices

import pytest
import gevent
import json
import base64
import werkzeug.security as wsecurity

import os
import time

app = gateway.app
gateway.api_users['TEST_USER'] = wsecurity.generate_password_hash('XXX_TEST_PASSWORD')

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
        assert 'text/plain' in r.content_type
        assert 'Unknown' in body
        assert 'unknown-door-id-666' in body


# TODO: parametrize
def test_missing_credentials_401(devices):
    with app.test_client() as c:
        r = c.post("doors/virtual-1/unlock?timeout=1.0")
        body = r.data.decode('utf8')
        assert 'text/plain' in r.content_type
        assert r.status_code == 401

def test_wrong_password_403(devices):
    with app.test_client() as c:
        r = c.post("doors/virtual-1/unlock?timeout=1.0", **authed(password='wrong'))
        body = r.data.decode('utf8')
        assert 'text/plain' in r.content_type
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


@pytest.fixture(scope="module")
def devices():
    gateway.mqtt_client = gateway.setup_mqtt_client()
    gevent.sleep(1) # ensure we are connected/subcribed before discovery
    testdevices.run()
    gevent.sleep(1) # let the devices spin up

@pytest.fixture(scope="module")
def mqtt_test_client():
    broker_url = os.environ.get('MSGFLO_BROKER', 'mqtt://localhost')
    mqtt_client, host, port = gateway.create_mqtt_client(broker_url)
    timeout = 5
    mqtt_client.connect(host, port, timeout)
    return mqtt_client


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

def test_xss_doorid(devices):
    with app.test_client() as c:
        r = c.post("doors/%3Cinput%20onfocus%3Dalert%281%29%20autofocus%3E/lock", **authed())
        body = r.data.decode('utf8')
        assert r.status_code != 200
        assert '<input ' not in body


# POST /door/id/lock
def test_lock_successful(devices):
    with app.test_client() as c:
        r = c.post("doors/virtual-1/lock", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 200
        assert 'text/plain' in r.content_type
        assert ' locked' in body

def test_lock_timeout(devices):
    with app.test_client() as c:
        r = c.post("doors/notresponding-1/lock?timeout=0.5", **authed())
        body = r.data.decode('utf8')
        assert 'text/plain' in r.content_type
        assert r.status_code == 504

def test_lock_errors(devices):
    with app.test_client() as c:
        r = c.post("doors/erroring-1/lock", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 502
        assert 'text/plain' in r.content_type
        assert 'error' in body
        assert 'fails always' in body

# GET /status
def test_status_missing_device_503(devices):
    with app.test_client() as c:
        r = c.get("status", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 503
        assert r.content_type == 'application/json'
        details = json.loads(body)
        assert details['doors']['sorenga-1']['status'] == 503
        assert details['doors']['virtual-1']['status'] == 200
        assert details['doors']['virtual-1']['last_seen'] >= 1512050000


def test_status_no_bolt_sensor(devices):
    door_id = 'virtual-1' # door without bolt sensor
    assert gateway.doors[door_id]

    with app.test_client() as c:
        r = c.get("status", **authed())
        details = json.loads(r.data.decode('utf8'))
        assert 'bolt' not in details['doors'][door_id], 'bolt information should not be present'


def test_status_bolt_sensor_changes(devices):
    door_id = 'virtual-2'
    gpio_number = 22

    def set_bolt_present(state : bool):
        device = 'doors/'+door_id
        testdevices.set_fake_gpio(device, gpio_number, state)
        gevent.sleep(0.5)

    with app.test_client() as c:
        test_start = time.time()
        set_bolt_present(False)

        set_bolt_present(True)
        r = c.get("status", **authed())
        details = json.loads(r.data.decode('utf8'))
        assert 'bolt' in details['doors'][door_id]
        bolt = details['doors'][door_id]['bolt']
        assert bolt['present']
        assert bolt['last_updated'] > test_start

        update_time = time.time()
        set_bolt_present(False)
        r = c.get("status", **authed())
        details = json.loads(r.data.decode('utf8'))
        assert 'bolt' in details['doors'][door_id]
        bolt = details['doors'][door_id]['bolt']
        assert not bolt['present']
        assert bolt['last_updated'] > update_time


not_running = list(set(gateway.doors.keys()) - set(testdevices.devices))
ignore = '&'.join('ignore={}'.format(d) for d in not_running)

def test_status_all_devices_ok(devices):
    with app.test_client() as c:
        r = c.get("status?" + ignore, **authed())
        body = r.data.decode('utf8')
        assert r.content_type == 'application/json'
        assert r.status_code == 200, body
        details = json.loads(body)
        statuses = [ d['status'] for d in details['doors'].values() ]
        assert statuses == [200] * len(statuses)
        assert 'sorenga-2' not in details['doors'].keys()

def test_status_seen_but_too_long_ago(devices):
    with app.test_client() as c:
        r = c.get("status?"+ignore+"&timeperiod=1", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 503, body
        details = json.loads(body)
        assert details['doors']['virtual-1']['status'] == 503

def test_invalid_fbp_message(devices, mqtt_test_client):
    '''should not influence future messages'''

    with app.test_client() as c:
        status_url = "status?"+ignore
        r = c.get(status_url, **authed())
        body = r.data.decode('utf8')
        assert r.content_type == 'application/json'
        assert r.status_code == 200, body

        # Send invalid message
        mqtt_test_client.publish('fbp', '{}')
        gevent.sleep(0.5)

        # check still works
        r = c.post("doors/virtual-1/unlock?duration=1", **authed())
        body = r.data.decode('utf8')
        assert r.status_code == 200
        # ensure is locked again at end of test
        gevent.sleep(1.1)


