
"""HTTP gateway for accessing doorlock functionality.

Communicates with the doorlock modules over MQTT
and presents a syncronous API.
"""

import gevent.monkey
gevent.monkey.patch_all() # make sure all syncronous calls in stdlib yields to gevent

import gevent.wsgi
import flask

import os

import paho.mqtt.client as mqtt

def send_mqtt():
    # TODO: keep client connected
    client = mqtt.Client()
    #client.username_pw_set(broker_info.username, broker_info.password)

    host = 'localhost'
    port = 1883
    client.connect(host, port, 60)

    # FIXME: unhardcode
    topic = "firmware/dlockoslo.py.UNLOCK"
    payload = '10'
    client.publish(topic, payload)

app = flask.Flask(__name__)
## System functionality
@app.route('/')
def index():
  return 'dlock-oslo HTTP gateway'

@app.route('/status')
def system_status():
    raise NotImplementedError("Unknown system status")


## Door functionality
@app.route('/doors/<doorid>/unlock', methods=['POST'])
def door_unlock(doorid):
    # FIXME: wait for and verify state change message
    send_mqtt()
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
    port = os.environ.get('PORT', 5000)
    ip = '127.0.0.1'  
    server = gevent.wsgi.WSGIServer((ip, port), app)
    print('Gateway running on {}:{}'.format(ip, port))    
    server.serve_forever()

if __name__ == "__main__":
    main()
