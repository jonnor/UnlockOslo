
import os
import os.path
import sys

firmware_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../firmware')
sys.path.insert(0, firmware_path)
import dlockoslo
import msgflo
import gevent

def set_fake_gpio(dev, number, state : bool):
    p = os.path.join(dev, 'gpio'+str(number))
    with open(p, 'w') as f:
        f.write('1' if state else '0')

def create_virtual_lock(name):
    os.environ['DLOCK_FAKE_GPIO'] = name
    lockdir = os.path.dirname(name)
    if not os.path.exists(lockdir):
        os.mkdir(lockdir)
    virtual = dlockoslo.LockParticipant(role=name)
    del os.environ['DLOCK_FAKE_GPIO']
    # turn door opener inputs off
    virtual.recalculate_state() # ensure files exist
    set_fake_gpio(name, 10, True)
    set_fake_gpio(name, 24, True)
    return virtual


def get_participants():
    participants = [
        create_virtual_lock('doors/virtual-1'),
        create_virtual_lock('doors/virtual-2'),
        create_virtual_lock('doors/dlock-2'),
        dlockoslo.AlwaysErroringParticipant(role='doors/erroring-1'),
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
