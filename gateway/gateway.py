
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

def mqtt_message_received(client, u, message):
    if message.topic != 'fbp':
        log_mqtt.warning('Unknown MQTT topic {}'.format(message.topic))

    d = message.payload.decode('utf8')
    m = json.loads(d)

    device = m['payload']['role']
    t = time.monotonic()
    log_mqtt.debug('saw device {} at {}'.format(device, t))
    m['time_received'] = t

    # Persist so we can query for device status
    if len(discovery_messages) == 100:
        # Remove the oldest to make space
        _oldest = discovery_messages.pop(0)
    discovery_messages.append(m)

def mqtt_subscribed(client, u, mid, granted_qos):
    log_mqtt.info('subscribed')

def mqtt_connected(client, u, f, rc):
    log_mqtt.info('connected')
    subscriptions = [
        ('fbp', 0),
    ]
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
    host = broker_info.hostname
    port = broker_info.port or 1883
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


def mqtt_send(topic, payload):
    client = mqtt_client
    client.publish(topic, payload)
    log_mqtt('sent', topic, payload)

def seen_since(messages, time : float):
    devices = {}
    for m in messages:
        d = m['payload']['role']
        t = m['time_received']
        if t > time:
            devices[d] = time
    return devices

app = flask.Flask(__name__)
doors = {
    'virtual-1': ('vitual-1',),
    'sorenga-1': ('sorenga-1',),
}

## System functionality
@app.route('/')
def index():
  return 'unlock-oslo HTTP gateway'

@app.route('/status')
def system_status():
    # TODO: allow specifying devices to ignore
    # TODO: allow specifying time interval
    since = time.monotonic() - 1*60
    seen_times = seen_since(discovery_messages, time=since)

    seen = set(seen_times.keys())
    expected = set(doors.keys())
    ignored = set([])
    missing = expected - (seen - ignored)
    unexpected = seen - expected

    if len(missing):
        return ("Missing heartbeat from {} devices: {}".format(len(missing), missing), 503)

    return "All {} door devices OK".format(len(expected))


## Door functionality
@app.route('/doors/<doorid>/unlock', methods=['POST'])
def door_unlock(doorid):
    try:
        door = doors[doorid]
    except KeyError:
        return ("Unknown door ID {}".format(doorid), 404)

    mqtt_prefix = door[0]

    topic = mqtt_prefix + "/unlock"
    payload = '10'
    send_mqtt(topic, payload)
    # FIXME: wait for and verify state change message
    return 'Door is now open'

@app.route('/doors/<doorid>/lock', methods=['POST'])
def door_lock(doorid):
    # FIXME: send lock message
    # FIXME: wait for and verify state change message
    return 'Door is now locked'

@app.route('/doors/<doorid>/state')
def door_state(doorid):
    # TODO: return current state of door, as reported on MQTT
    raise NotImplementedError("Unknown system status")


def main():
    # Make sure we are connected to MQTT even though no requests have come in
    mqtt_client = create_client()

    port = os.environ.get('PORT', 5000)
    ip = '127.0.0.1'  
    server = gevent.wsgi.WSGIServer((ip, port), app)
    log.info('Gateway running on {}:{}'.format(ip, port))
    server.serve_forever()

if __name__ == "__main__":
    main()
