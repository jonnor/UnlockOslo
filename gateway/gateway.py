
"""HTTP gateway for accessing doorlock functionality.

Communicates with the doorlock modules over MQTT
and presents a syncronous API.
"""

import gevent.monkey
gevent.monkey.patch_all() # make sure all syncronous calls in stdlib yields to gevent

import gevent.wsgi
import flask

import os


app = flask.Flask(__name__)
## System functionality
@app.route('/')
def index():
  return 'dlock-oslo gateway'

@app.route('/status')
def system_status():
    raise NotImplementedError("Unknown system status")


## Door functionality
@app.route('/doors/<doorid>/unlock', methods=['POST'])
def door_unlock(doorid):
    return 'Hello World'

@app.route('/doors/<doorid>/lock', methods=['POST'])
def door_lock(doorid):
    return 'Hello World'

@app.route('/doors/<doorid>/state')
def door_state(doorid):
    raise NotImplementedError("Unknown system status")


def main():
    port = os.environ.get('PORT', 5000)
    ip = '127.0.0.1'  
    server = gevent.wsgi.WSGIServer((ip, port), app)
    print('Gateway running on {}:{}'.format(ip, port))    
    server.serve_forever()

if __name__ == "__main__":
    main()
