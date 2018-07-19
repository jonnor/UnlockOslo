import dlockoslo
import time
import sys

"""Tool for testing the hardware board

Uses I/O utilities and pin definitions from firmware,
to also ensure that these are correct"""

def check_inputs(delay):
    print('check inputs')
    for number, pin in dlockoslo.ins.items():
        print('setup', number, pin)
        dlockoslo.setup_gpio_pin(pin, 'in')

    while True:
        c = []
        for number, pin in dlockoslo.ins.items():
            p = dlockoslo.gpio_file_path(pin)
            s = dlockoslo.read_boolean(p)
            c.append(s)
        print(c)
        time.sleep(delay)

def check_outputs(delay):
    print('check outputs')
    for number, pin in dlockoslo.outs.items():
        print('setup', number, pin)
        dlockoslo.setup_gpio_pin(pin, 'out')

    state = False
    while True:
        c = []
        for number, pin in dlockoslo.outs.items():
            p = dlockoslo.gpio_file_path(pin)
            print('writing to', p, state)
            dlockoslo.set_gpio(p, state)
            time.sleep(delay)
        state = not state

def check_status(delay):
    print('check status leds')
    for number, pin in dlockoslo.status.items():
        print('setup', number, pin)
        dlockoslo.setup_gpio_pin(pin, 'out')

    state = False
    while True:
        c = []
        for number, pin in dlockoslo.status.items():
            p = dlockoslo.gpio_file_path(pin)
            print('writing to', p, state)
            dlockoslo.set_gpio(p, state)
            time.sleep(delay)
        state = not state

# NOTE: could do an automated test by connecting each output to corresponding input,
# then generating output patterns and ensuring that they are read correctly on input
def main():
    prog, args = sys.argv[0], sys.argv[1:]

    mode = 'input'
    if len(args) >= 1:
        mode = args[0]
    delay = 0.15
    if len(args) >= 2:
        delay = float(args[1])

    if 'output' in mode:
        check_outputs(delay)
    elif 'status' in mode:
        check_status(delay)
    elif 'input' in mode:
        check_inputs(delay)

if __name__ == '__main__':
    main()
