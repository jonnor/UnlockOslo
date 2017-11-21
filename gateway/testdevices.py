
import os
import os.path
import sys

firmware_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../firmware')
sys.path.insert(0, firmware_path)
import dlockoslo
import msgflo
import gevent

def create_virtual_lock(name):
    os.environ['DLOCK_FAKE_GPIO'] = name
    if not os.path.exists(name):
        os.mkdir(name)
    virtual = dlockoslo.LockParticipant(role=name)
    del os.environ['DLOCK_FAKE_GPIO']
    return virtual


def get_participants():
    participants = [
        create_virtual_lock('virtual-1'),
        create_virtual_lock('virtual-2'),
        dlockoslo.AlwaysErroringParticipant(role='erroring-1'),
    ]
    # for emulating timeout/device missing, send on MQTT topic which nothing uses
    return participants

def run(done_cb=None):
    participants = get_participants()
    engine = msgflo.run(participants, done_cb=done_cb)
    return participants, engine

def main():
    participants = get_participants()
    waiter = gevent.event.AsyncResult()
    engine = msgflo.run(participants, done_cb=waiter.set)
    waiter.wait()

if __name__ == '__main__':
    main()
