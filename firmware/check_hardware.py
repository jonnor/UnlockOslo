import dlockoslo
import time
import sys

"""Tool for testing the hardware board

Uses I/O utilities and pin definitions from firmware,
to also ensure that these are correct"""

def check_inputs():
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
        time.sleep(0.2)

def check_outputs():
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
            time.sleep(0.15)
        state = not state

# NOTE: could do an automated test by connecting each output to corresponding input,
# then generating output patterns and ensuring that they are read correctly on input
def main():
    prog, args = sys.argv[0], sys.argv[1:]
    if len(args) and 'output' in args[0]:
        check_outputs()
    else:
        check_inputs()

if __name__ == '__main__':
    main()
