
"""HTTP gateway for accessing doorlock functionality.

Communicates with the doorlock modules over MQTT
and presents a syncronous API.
"""

import gevent.monkey
gevent.monkey.patch_all() # make sure all syncronous calls in stdlib yields to gevent

import gevent.wsgi
import flask
import paho.mqtt.client as mqtt

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


discovery_messages = []
mqtt_client = None
mqtt_message_waiters = [] # queue instances

allowed_ips = os.environ.get('DLOCK_ALLOWED_IPS', '127.0.0.1').split(',')
if allowed_ips == ['*']:
    # Allowed from everywhere
    allowed_ips = None

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
        if len(discovery_messages) == 100:
            # Remove the oldest to make space
            _oldest = discovery_messages.pop(0)
        discovery_messages.append(m)
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

def mqtt_connected(client, u, f, rc):
    log_mqtt.info('connected')
    subscriptions = [
        ('fbp', 0),
    ]
   
    out_topics = ('islocked', 'isopen', 'error')
    for doorid, door in doors.items():
        basetopic = door[0]
        for t in out_topics:
            topic = "{}/{}".format(basetopic, t)
            subscriptions.append((topic, 0))

    client.subscribe(subscriptions)
    log_mqtt.info('subscribe()')

def create_client():
    broker_url = os.environ.get('MSGFLO_BROKER', 'mqtt://localhost')
    broker_info = urlparse(broker_url)

    client = mqtt.Client()
    if broker_info.username:
        client.username_pw_set(broker_info.username, broker_info.password)
    client.on_connect = mqtt_connected
    client.on_message = mqtt_message_received
    client.on_subscribe = mqtt_subscribed
    host = broker_info.hostname
    default_port = 1883
    if broker_info.scheme == 'mqtts':
        default_port = 8883
        client.tls_set()
    port = broker_info.port or default_port
    client.connect(host, port, 60)
    log_mqtt.info('connect() done')

    def _mqtt_loop():
        while True:
            try:
                # Pump
                client.loop(timeout=0.2)
                # Yield to other greenlets so they don't starve
                gevent.sleep(0.2)
            finally:
                pass
    gevent.Greenlet.spawn(_mqtt_loop)

    return client

def mqtt_send(topic, payload):
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = create_client()

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
        if door[0] == role:
            return doorid
    return None

def require_allowed_ip(f):
    def check_ip(ip):
        if allowed_ips is None:
            # allow all
            return True
        return ip in allowed_ips

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        remote = flask.request.environ['REMOTE_ADDR']
        ip = flask.request.headers.get('X-Real-IP', remote)
        if not check_ip(ip):
            return ("Access denied", 403)
        return f(*args, **kwargs)
    return decorated

def require_basic_auth(f):
    def check_auth(username, password):
        actual_password = api_users.get(username, '')
        return actual_password == password

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = flask.request.authorization
        if not auth:
            return ("Missing Authorization", 401)
        if not check_auth(auth.username, auth.password):
            return ("Wrong Authorization", 403)
        return f(*args, **kwargs)
    return decorated

app = flask.Flask(__name__)
api_users = {}
doors = {
    'virtual-1': ('doors/virtual-1',),
    'virtual-2': ('doors/virtual-2',),
    'erroring-1': ('doors/erroring-1',),
    'notresponding-1': ('doors/notresponding-1',),
    'sorenga-1': ('doors/dlock-1',),
    'hotspare-1': ('doors/dlock-2',),
}

## System functionality
# No auth
@app.route('/')
def index():
  return 'UnlockOslo device gateway'

# No auth for easy integration with monitoring tools/services
@app.route('/status')
def system_status():
    timeperiod = float(flask.request.args.get('timeperiod', '60'))
    assert_not_outside(timeperiod, 1, 10*60)

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
    door_mqtt_roles = [ d[0] for d in doors.items() ]
    expected = set(door_mqtt_roles)
    checked = expected - ignored
    missing = checked - seen
    unexpected = seen - expected

    def door_data(doorid):
        status = 200 if doorid in seen else 503
        last_seen = seen_times.get(doors[doorid][0])
        return { 'status': status, 'last_seen': last_seen }

    details = {
        'doors': { doorid: door_data(doorid) for doorid in checked }
    }
    if len(missing):
        return flask.jsonify(details), 503

    return flask.jsonify(details), 200


def assert_not_outside(value, lower, upper):
  between = lower <= value <= upper
  if not between:
      raise ValueError("{} is outside [{}, {}]".format(value, lower, upper))

## Door functionality
@app.route('/doors/<doorid>/unlock', methods=['POST'])
@require_allowed_ip
@require_basic_auth
def door_unlock(doorid):
    try:
        door = doors[doorid]
    except KeyError:
        return ("Unknown door ID {}".format(doorid), 404)

    try:
        timeout = float(flask.request.args.get('timeout', '5.0'))
        assert_not_outside(timeout, 0.1, 60.0)
    except ValueError:
        return ("Invalid timeout specified", 422)

    try:
        duration = flask.request.args.get('duration', None)
        if duration:
          duration = int(duration)
          assert_not_outside(duration, 1, 10*60)
    except ValueError as e:
        return ("Invalid duration: {}".format(e), 422)

    mqtt_prefix = door[0]
    # Subscribe
    def unlock_or_error(topic, data):
        iserror = topic == mqtt_prefix+'/error'
        isunlocked = topic == mqtt_prefix+'/islocked' and data == 'false'
        return iserror or isunlocked
    wait_response = MessageWaiter(unlock_or_error)
    mqtt_message_waiters.append(wait_response)

    # Send message to request unlocking
    payload = 'true' if duration is None else str(duration)
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
@require_allowed_ip
@require_basic_auth
def door_lock(doorid):
    try:
        door = doors[doorid]
    except KeyError:
        return ("Unknown door ID {}".format(doorid), 404)

    try:
        timeout = float(flask.request.args.get('timeout', '5.0'))
        assert_not_outside(timeout, 0.1, 60.0)
    except ValueError:
        return ("Invalid timeout specified", 422)

    mqtt_prefix = door[0]
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
@require_allowed_ip
@require_basic_auth
def door_state(doorid):
    try:
        door = doors[doorid]
    except KeyError:
        return ("Unknown door ID {}".format(doorid), 404)

    # TODO: return current state of door, as reported on MQTT
    raise NotImplementedError("Unknown system status")

def read_auth_db():
    e = os.environ.get('DLOCK_API_CREDENTIALS', '')
    for credentials in e.split(','):
      if credentials:
        user, pw = credentials.split(':')
        api_users[user] = pw

def main():
    # Make sure we are connected to MQTT even though no requests have come in
    mqtt_client = create_client()
    read_auth_db()

    port = os.environ.get('PORT', 5000)
    ip = os.environ.get('INTERFACE', '127.0.0.1')
    server = gevent.wsgi.WSGIServer((ip, port), app)
    log.info('Gateway running on {}:{}'.format(ip, port))
    server.serve_forever()

if __name__ == "__main__":
    main()
