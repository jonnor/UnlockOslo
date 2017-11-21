
import os
import os.path
import sys

sys.path.insert(0, './firmware')
import dlockoslo
import msgflo

def create_virtual_lock(name):
    os.environ['DLOCK_FAKE_GPIO'] = name
    if not os.path.exists(name):
        os.mkdir(name)
    virtual = msgflo.main(dlockoslo.LockParticipant, role=name)
    del os.environ['DLOCK_FAKE_GPIO']
    return virtual

def main():
    virtual1 = create_virtual_lock('virtual-1')
    virtual2 = create_virtual_lock('virtual-2')
    erroring = msgflo.main(dlockoslo.AlwaysErroringParticipant, role='erroring-1')
    # for emulating timeout/device missing, send on MQTT topic which nothing

if __name__ == '__main__':
    print(__file__)
    main()
