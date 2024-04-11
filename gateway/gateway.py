
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
import structlog 

from urllib.parse import urlparse
import os
import json
import time
import queue
import functools
import logging
import uuid

def make_id():
    import datetime
    import uuid

    t = datetime.datetime.now().strftime('%Y%m%d-%H%M') 
    u = str(uuid.uuid4())[0:4]
    id = f'{t}-{u}'
    return id

def configure_logging(log_path, filename=None):
    
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    if filename is None:
        filename = f'{make_id()}.gateway.log'

    key_order = ['door', 'method', 'path', 'user', 'request_id', 'topic', 'payload']

    # FIXME: add timestamping
    structlog.configure(
        processors=[
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(),
    )

    file_formatter = structlog.stdlib.ProcessorFormatter(
        structlog.processors.KeyValueRenderer(key_order=key_order, drop_missing=True)
    )

    file = logging.FileHandler(filename)
    stdout = logging.StreamHandler() 

    stdout.setFormatter(formatter)
    file.setFormatter(file_formatter)

    logging.basicConfig(
        format="%(message)s",
        level=logging.DEBUG,
        handlers=[file, stdout],
    )


log_path = os.environ.get('DLOCK_LOG_PATH', 'logs')

configure_logging(log_path)

log = structlog.get_logger()


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
            log.warning('MesssageWaiter: Exception match check: {}'.format(e))

def mqtt_message_received(client, u, message):
    try:
        mqtt_handle_message(client, u, message)
    except Exception as e:
        log.exception('Failed to handle message %: %s '.format(message.topic, message.payload))

def door_id_from_mqtt(prefix):
    door_id = None
    for d, info in doors.items():
        if info.mqtt_prefix == prefix:
            door_id = d
    return door_id


def elide(data, length=30, suffix=b'...'):
    return (data[:length] + suffix) if len(data) > length else data

def mqtt_handle_message(client, u, message):

    start_time = time.time()
    matches = []
    door = door_from_topic(message.topic)

    if message.topic == 'fbp':
        # Heartbeat messages
        d = message.payload.decode('utf8')
        m = json.loads(d)

        device = m['payload']['role']
        door = door_id_from_mqtt(device)
        t = time.time()
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
        # Only set last_updated if state actually changed
        status = door_bolt_status.get(door_id, None)
        if status is None or (present != status.present):
            door_bolt_status[door_id] = DoorBoltStatus(present, time.time())

    else:
        # Check responses
        for waiter in mqtt_message_waiters: 
            m = waiter.check_match(message.topic, message.payload.decode('utf8'))
            if m:
                matches.append(m)

    end_time = time.time()

    duration = 1000.0*(end_time-start_time)
    payload = elide(message.payload)

    log.info('mqtt-receive',
            door=door,
            topic=message.topic,
            payload=payload,
            duration_ms=duration,
            matches=len(matches),
            waiters=len(mqtt_message_waiters),
    )


def mqtt_subscribed(client, u, mid, granted_qos):
    log.info('mqtt-subscribed', mid=mid)

def mqtt_disconnected(client, u, rc):
    log.info('mqtt-disconnected', rc=rc)
    # client automatically handles reconnect

def mqtt_connected(client, u, f, rc):
    log.info('mqtt-connected', rc=rc)
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

def setup_mqtt_client():
    broker_url = os.environ.get('MSGFLO_BROKER', 'mqtt://localhost')
    client, host, port = create_mqtt_client(broker_url)

    client.on_connect = mqtt_connected
    client.on_disconnect = mqtt_disconnected
    client.on_message = mqtt_message_received
    client.on_subscribe = mqtt_subscribed

    client.connect(host, port, 60)
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

    door = door_from_topic(topic)
    # FIXME: also provide request_id
    log.info('mqtt-send', door=door, topic=topic, payload=payload)

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
    'sorenga-1': DoorInfo('doors/dlock-1', bolt_sensor=True),
    'hotspare-1': DoorInfo('doors/dlock-2'),
    'fubiak-1': DoorInfo('doors/dlock-3'),
    'unused-4': DoorInfo('doors/dlock-4'),
    'origo-1': DoorInfo('doors/dlock-5'),
    'origo-2': DoorInfo('doors/dlock-6'),
    'lindeberg-1': DoorInfo('doors/dlock-7'),
    'deichman-majorstuen': DoorInfo('doors/dlock-8'),
    'loren-1': DoorInfo('doors/dlock-9', bolt_sensor=True),
    'deichman-toyen': DoorInfo('doors/dlock-10'),
    'deichman-stovner': DoorInfo('doors/dlock-11'),
    'deichman-oppsal': DoorInfo('doors/dlock-12'),
    'deichman-nordtvet': DoorInfo('doors/dlock-13'),
    'nordreaker-rachelgrepp-1': DoorInfo('doors/dlock-14'),
    'stovnerskogen-1': DoorInfo('doors/dlock-15'),
    'midtasen-1': DoorInfo('doors/dlock-16'),
    'deichman-bjerke': DoorInfo('doors/dlock-17'),
    'stovnerskogen-2': DoorInfo('doors/dlock-18'),
    'midtasen-2': DoorInfo('doors/dlock-19'),
    'deichman-grunerlokka': DoorInfo('doors/dlock-20'),
    'slurpen-1': DoorInfo('doors/dlock-21'),
    'unused-22': DoorInfo('doors/dlock-22'),
    'unused-23': DoorInfo('doors/dlock-23'),
    'unused-24': DoorInfo('doors/dlock-24'),
    'unused-25': DoorInfo('doors/dlock-25'),
    'deichman-bjorvika': DoorInfo('doors/dlock-26'),
    'unused-27': DoorInfo('doors/dlock-27'),
    'baerum-kommune-1': DoorInfo('doors/dlock-28'),
    'baerum-kommune-2': DoorInfo('doors/dlock-29'),
    'deichman-boler': DoorInfo('doors/dlock-30'),
    'deichman-nydalen': DoorInfo('doors/dlock-31'),
    'deichman-torshov': DoorInfo('doors/dlock-32'),
    'unused-33': DoorInfo('doors/dlock-33'),
    'unused-34': DoorInfo('doors/dlock-34'),
    'rachel-grepp-1': DoorInfo('doors/dlock-35'),
    'unused-36': DoorInfo('doors/dlock-36'),
    'haugen-skole-1': DoorInfo('doors/dlock-37'),
    'unused-38': DoorInfo('doors/dlock-38'),
    'rachel-grepp-2': DoorInfo('doors/dlock-39'),
    'rachel-grepp-3': DoorInfo('doors/dlock-40'),
    'nordreaker-n21-1': DoorInfo('doors/dlock-41'),
    'unused-42': DoorInfo('doors/dlock-42'),
    'unused-43': DoorInfo('doors/dlock-43'),
    'unused-44': DoorInfo('doors/dlock-44'),
    'unused-45': DoorInfo('doors/dlock-45')
}
api_users = {}


def door_from_path(path):
    # /doors/virtual-1/unlock?...
    if not path.startswith('/doors'):
        return None

    tok = path.split('/')
    door = tok[2]
    return door

def door_from_topic(topic):
    # doors/device-100/unlock
    #m = re.match(r"doors\/(.*)\/.*")
    tok = topic.split('/')
    if len(tok) <= 2:
        return None
    prefix = '/'.join(tok[0:2])
    door = door_id_from_mqtt(prefix)
    return door

def request_log_params():
    r, g = flask.request, flask.g

    user = None if not r.authorization else r.authorization.username
    query = f'{r.path}?{r.query_string.decode("utf-8")}'
    door = door_from_path(r.path)

    log_params = dict(
        request_id=g.request_id,
        method=r.method,
        path=query,
        user=user,
        door=door,
    )
    return log_params


## Logging helpers
def log_request(sender, **extra):
    r, g = flask.request, flask.g

    # add info
    g.request_id = r.headers.get('X-Request-Id', str(uuid.uuid4()))
    g.request_start_time = time.time()

    log_params = request_log_params()
    log_params.update(dict(
    ))

    log.info('http-request-start', **log_params)

def log_response(sender, response, **extra):
    r, g = flask.request, flask.g

    g.request_end_time = time.time()
    duration = 1000.0 * (flask.g.request_end_time - flask.g.request_start_time)

    log_params = request_log_params()
    log_params.update(dict(
        status_code=response.status_code,
        duration_ms=duration,
    ))

    log.info('http-request-end', **log_params)


flask.request_started.connect(log_request, app)
flask.request_finished.connect(log_response, app)


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
    server = gevent.pywsgi.WSGIServer((ip, port), app, log=None)
    log.info('started', ip=ip, port=port)
    server.serve_forever()

if __name__ == "__main__":
    main()
