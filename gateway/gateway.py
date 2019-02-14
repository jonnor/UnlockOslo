
"""HTTP gateway for accessing doorlock functionality.

Communicates with the doorlock modules over MQTT
and presents a syncronous API.
"""

import gevent.monkey
gevent.monkey.patch_all() # make sure all syncronous calls in stdlib yields to gevent

import gevent.pywsgi
import flask
import paho.mqtt.client as mqtt
import werkzeug.security as wsecurity

from urllib.parse import urlparse
import os
import json
import time
import queue
import functools

import logging
logging.basicConfig()
log_level = os.environ.get('LOGLEVEL', 'info')
level = getattr(logging, log_level.upper())

log_mqtt = logging.getLogger('mqtt')
log_mqtt.setLevel(level)
log = logging.getLogger('gateway')
log.setLevel(level)


class DoorBoltStatus:
    def __init__(self,
                 present: bool,
                 last_update: float):
        self.present = present
        self.last_update = last_update


door_bolt_status = {}
discovery_messages = []
mqtt_client = None
mqtt_message_waiters = [] # queue instances

class MessageWaiter():
    def __init__(self, matcher, _queue=None):
        if _queue is None:
            _queue = queue.Queue()
        self.queue = _queue
        self.matcher = matcher

    def check_match(self, topic, data):
        try:
            match = self.matcher(topic, data)
            if match:
                self.queue.put((topic, data))
            return match
        except Exception as e:
            log_mqtt.warning('MesssageWaiter: Exception match check: {}'.format(e))

def mqtt_message_received(client, u, message):
    try:
        mqtt_handle_message(client, u, message)
    except Exception as e:
        log_mqtt.exception('Failed to handle message %: %s '.format(message.topic, message.payload))

def door_id_from_mqtt(prefix):
    door_id = None
    for d, info in doors.items():
        if info.mqtt_prefix == prefix:
            door_id = d
    return door_id

def mqtt_handle_message(client, u, message):
    log_mqtt.debug('received {}: {}'.format(message.topic, message.payload))

    if message.topic == 'fbp':
        # Heartbeat messages
        d = message.payload.decode('utf8')
        m = json.loads(d)

        device = m['payload']['role']
        t = time.time()
        log_mqtt.debug('saw device {} at {}'.format(device, t))
        m['time_received'] = t

        # Persist so we can query for device status
        if len(discovery_messages) == 2000:
            # Remove the oldest to make space
            _oldest = discovery_messages.pop(0)
        discovery_messages.append(m)

    elif message.topic.endswith('/boltpresent'):
        # Updates about door presence status
        mqtt_prefix = message.topic.rstrip('/boltpresent')
        door_id = door_id_from_mqtt(mqtt_prefix)
        payload = message.payload.decode('utf8')
        present = (payload == 'true')
        print('door presence change', mqtt_prefix, door_id, payload)
        door_bolt_status[door_id] = DoorBoltStatus(present, time.time())

    else:
        # Check responses
        matches = []
        for waiter in mqtt_message_waiters: 
            m = waiter.check_match(message.topic, message.payload.decode('utf8'))
            if m:
                matches.append(m)
        if len(matches) == 0:
            log_mqtt.debug('No matches for message on: {}. {} waiters'.format(message.topic, len(mqtt_message_waiters)))


def mqtt_subscribed(client, u, mid, granted_qos):
    log_mqtt.info('subscribed')

def mqtt_disconnected(client, u, rc):
    log_mqtt.info('disconnected: {}'.format(rc))
    # client automatically handles reconnect

def mqtt_connected(client, u, f, rc):
    log_mqtt.info('connected')
    subscriptions = [
        ('fbp', 0),
    ]
   
    out_topics = ('islocked', 'isopen', 'error', 'boltpresent')
    for doorid, door in doors.items():
        basetopic = door.mqtt_prefix
        for t in out_topics:
            topic = "{}/{}".format(basetopic, t)
            subscriptions.append((topic, 0))

    client.subscribe(subscriptions)
    log_mqtt.info('subscribe()')

def setup_mqtt_client():
    broker_url = os.environ.get('MSGFLO_BROKER', 'mqtt://localhost')
    client, host, port = create_mqtt_client(broker_url)

    client.on_connect = mqtt_connected
    client.on_disconnect = mqtt_disconnected
    client.on_message = mqtt_message_received
    client.on_subscribe = mqtt_subscribed

    client.connect(host, port, 60)
    log_mqtt.info('connect() done')
    return client

def create_mqtt_client(broker_url):
    broker_info = urlparse(broker_url)

    client = mqtt.Client()
    if broker_info.username:
        client.username_pw_set(broker_info.username, broker_info.password)

    client.reconnect_delay_set(min_delay=1, max_delay=2*60)

    host = broker_info.hostname
    default_port = 1883
    if broker_info.scheme == 'mqtts':
        default_port = 8883
        client.tls_set()
    port = broker_info.port or default_port

    # XXX loop() does not handle reconnects, have to use loop_start() or loop_forever() 
    client.loop_start()

    return client, host, port

def mqtt_send(topic, payload):
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = setup_mqtt_client()

    client = mqtt_client
    client.publish(topic, payload)
    log_mqtt.debug('sent {}: {}'.format(topic, payload))

def seen_since(messages, time : float):
    devices = {}
    for m in messages:
        d = m['payload']['role']
        t = m['time_received']
        if t > time:
            devices[d] = t
    return devices

def find_door_id(role):
    for doorid, door in doors.items():
        if door.mqtt_prefix == role:
            return doorid
    return None

def require_basic_auth(f):
    def check_auth(username, password):
        found_hash = api_users.get(username, None)
        if found_hash is None:
            return False
        return wsecurity.check_password_hash(found_hash, password)

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = flask.request.authorization
        if not auth:
            return ("Missing Authorization", 401)
        if not check_auth(auth.username, auth.password):
            return ("Wrong Authorization", 403)
        return f(*args, **kwargs)
    return decorated

def returns_content_type(mime_type):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            content, code = f(*args, **kwargs)
            return flask.Response(content, code, mimetype=mime_type)
        return decorated_function
    return decorator

class DoorInfo():
    """Information about each door. Rarely changing, not stateful"""
    def __init__(self, mqtt_prefix, bolt_sensor=False):

        self.mqtt_prefix = mqtt_prefix
        self.bolt_sensor = bolt_sensor


app = flask.Flask(__name__)
# TODO: load from database
doors = {
    'virtual-1': DoorInfo('doors/virtual-1'),
    'virtual-2': DoorInfo('doors/virtual-2', bolt_sensor=True),
    'erroring-1': DoorInfo('doors/erroring-1'),
    'notresponding-1': DoorInfo('doors/notresponding-1'),
    'dev-0': DoorInfo('doors/dlock-0'),
    'sorenga-1': DoorInfo('doors/dlock-1'),
    'hotspare-1': DoorInfo('doors/dlock-2'),
    'fubiak-1': DoorInfo('doors/dlock-3'),
    'unused-4': DoorInfo('doors/dlock-4'),
    'origo-1': DoorInfo('doors/dlock-5'),
    'origo-2': DoorInfo('doors/dlock-6'),
    'lindeberg-1': DoorInfo('doors/dlock-7'),
    'unused-8': DoorInfo('doors/dlock-8'),
    'loren-1': DoorInfo('doors/dlock-9'),
    'unused-10': DoorInfo('doors/dlock-10'),
    'unused-11': DoorInfo('doors/dlock-11'),
    'unused-12': DoorInfo('doors/dlock-12'),
    'unused-13': DoorInfo('doors/dlock-13'),
}
api_users = {}

## System functionality
# No auth
@app.route('/')
def index():
  return 'UnlockOslo device gateway'


@app.route('/status')
@require_basic_auth
def system_status():
    timeperiod = float(flask.request.args.get('timeperiod', '600'))
    assert_not_outside(timeperiod, 1, 60*60)

    default_ignore = os.environ.get('DLOCK_IGNORE_MISSING', 'notresponding-1').split(',')
    ignored = flask.request.args.getlist('ignore')
    if len(ignored) == 0:
        ignored = default_ignore
    ignored = set(ignored)

    # Check which devices we've seen and not
    since = time.time() - timeperiod
    seen_times = seen_since(discovery_messages, time=since)
    seen_doors = [ find_door_id(r) for r in seen_times.keys() if find_door_id(r) ]

    seen = set(seen_doors)
    door_mqtt_roles = [ d for d in doors.keys() ]
    expected = set(door_mqtt_roles)
    checked = expected - ignored
    missing = checked - seen
    unexpected = seen - expected

    def door_data(doorid):
        status = 200 if doorid in seen else 503
        last_seen = seen_times.get(doors[doorid].mqtt_prefix)
        info = {
            'status': status,
            'last_seen': last_seen,
        }
        has_bolt_sensor = doors[doorid].bolt_sensor
        bolt_status = door_bolt_status.get(doorid, None)
        if has_bolt_sensor:
            info['bolt'] = {
                'present': bolt_status.present if bolt_status else None,
                'last_updated': bolt_status.last_update if bolt_status else None,
            }

        return info

    details = {
        'doors': { doorid: door_data(doorid) for doorid in checked }
    }
    if len(missing):
        return flask.jsonify(details), 503

    return flask.jsonify(details), 200


def assert_not_outside(value, lower, upper):
  between = lower <= value <= upper
  if not between:
      m = "{} is outside [{}, {}]".format(value, lower, upper)
      raise ValueError(flask.escape(m))

## Door functionality
@app.route('/doors/<doorid>/unlock', methods=['POST'])
@returns_content_type('text/plain')
@require_basic_auth
def door_unlock(doorid):
    try:
        door = doors[doorid]
    except KeyError:
        return ("Unknown door ID {}".format(flask.escape(doorid)), 404)

    try:
        timeout = float(flask.request.args.get('timeout', '5.0'))
        assert_not_outside(timeout, 0.1, 60.0)
    except ValueError:
        return ("Invalid timeout specified", 422)

    try:
        duration = int(flask.request.args.get('duration', '2'))
        assert_not_outside(duration, 1, 10*60)
    except ValueError as e:
        return ("Invalid duration: {}".format(flask.escape(str(e))), 422)

    mqtt_prefix = door.mqtt_prefix
    # Subscribe
    def unlock_or_error(topic, data):
        iserror = topic == mqtt_prefix+'/error'
        isunlocked = topic == mqtt_prefix+'/islocked' and data == 'false'
        return iserror or isunlocked
    wait_response = MessageWaiter(unlock_or_error)
    mqtt_message_waiters.append(wait_response)

    # Send message to request unlocking
    payload = str(duration)
    mqtt_send(mqtt_prefix + "/unlock", payload)

    # Wait for response
    topic, data, timedout = None, None, None
    try:
        topic, data = wait_response.queue.get(block=True, timeout=timeout)
    except queue.Empty:
        timedout = ('Door did not respond in time', 504)

    # Handle response
    mqtt_message_waiters.remove(wait_response)
    if timedout:
      return timedout

    is_error = topic.endswith('/error') 
    if is_error:
      return ("Door unlock error: {}".format(data), 502)

    return ('Door is now unlocked', 200)


@app.route('/doors/<doorid>/lock', methods=['POST'])
@returns_content_type('text/plain')
@require_basic_auth
def door_lock(doorid):
    try:
        door = doors[doorid]
    except KeyError:
        return ("Unknown door ID {}".format(flask.escape(doorid)), 404)

    try:
        timeout = float(flask.request.args.get('timeout', '5.0'))
        assert_not_outside(timeout, 0.1, 60.0)
    except ValueError:
        return ("Invalid timeout specified", 422)

    mqtt_prefix = door.mqtt_prefix
    # Subscribe
    def locked_or_error(topic, data):
        iserror = topic == mqtt_prefix+'/error'
        islocked = topic == mqtt_prefix+'/islocked' and data == 'true'
        return iserror or islocked
    wait_response = MessageWaiter(locked_or_error)
    mqtt_message_waiters.append(wait_response)

    # Send message to request unlocking
    mqtt_send(mqtt_prefix + "/lock", "true")

    # Wait for response
    topic, data, timedout = None, None, None
    try:
        topic, data = wait_response.queue.get(block=True, timeout=timeout)
    except queue.Empty:
        timedout = ('Door did not respond in time', 504)

    # Handle response
    mqtt_message_waiters.remove(wait_response)
    if timedout:
      return timedout

    if topic.endswith('/error') :
      return ("Door lock error: {}".format(data), 502)

    return ('Door is now locked', 200)


@app.route('/doors/<doorid>/state')
@returns_content_type('text/plain')
@require_basic_auth
def door_state(doorid):
    try:
        door = doors[doorid]
    except KeyError:
        return ("Unknown door ID {}".format(flask.escape(doorid)), 404)

    # TODO: return current state of door, as reported on MQTT
    raise NotImplementedError("Unknown system status")

def read_auth_db():
    e = os.environ.get('DLOCK_API_CREDENTIALS', '')
    for credentials in e.split(','):
      if credentials:
        user, pw = credentials.split(';')
        api_users[user] = pw

def main():
    # Make sure we are connected to MQTT even though no requests have come in
    mqtt_client = setup_mqtt_client()
    read_auth_db()

    port = os.environ.get('PORT', 5000)
    ip = os.environ.get('INTERFACE', '127.0.0.1')
    server = gevent.pywsgi.WSGIServer((ip, port), app)
    log.info('Gateway running on {}:{}'.format(ip, port))
    server.serve_forever()

if __name__ == "__main__":
    main()
