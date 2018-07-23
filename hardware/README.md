# Bill of materials

* RPi,enclosure etc. [Digikey BOM](./assembly.csv)
* UnlockOslo RPi hat. [Digikey BOM](./alpha-1/production/) 
* wiring
* Ethernet cable

# Enclosure

3d-model. [FreeCAD source](./enclosure.fcstd)

![Enclosure when installed](./docs/enclosure-installed.jpg)

# UnlockOslo Hat "alpha"

The "alpha" board is a Hat for Raspberry Pi boards. Main features:

* Step down converter to 5 V, 2 A. This is enough to power the
  Raspberry Pi board.
* 8 inputs, supports up to 24 V inputs.
* 6 outputs, the output voltage is the same as input voltage. LEDs
  indicate the pin's status.
* On-board temperature sensor.
* Two status LEDs, controlled by GPIO.
* The serial port is broken out on its own header. Useful for
  low-level rpi debugging.
* 5 V and 3 V rails are broken out to a separate power header. The 3 V
  rail is from the rpi regulator.

## alpha-3

Improved version of alpha-1. Fixed bugs, added reverse polarity
protection. Produced by PCBway, assembled at Bitraf.

[KiCad project](./alpha-1)

### Schematic

[![Schematics](./docs/alpha-3-schematic.png)](./docs/alpha-3-schematic.pdf)

## alpha-2

An experiment into if it was possible to include an esp8266 on the
board while keeping it RPi hat compatible. Conclusion: Almost
possible.

## alpha-1

Original version. Deployed at two locations.

[KiCad project](./alpha-1)

### Schematic

[![Schematics](./docs/alpha-1-schematic.png)](./docs/alpha-1-schematic.pdf)

All components available from Digikey.

The PCB has been successfully produced by PCBWay, and assembled at Bitraf.

### PCB testing procedure

A testing script exists for checking the inputs, outputs and status LEDs.
This is intended to run on the Rasperry PI setup in the normal way (see [firmware](./firmware) for setup).

First stop the firmware service temporarily

    sudo systemctl stop dlock-firmware

Move to firmware dir and change user

    sudo su dlock
    cd /opt/dlock/src

Check the inputs

    ./venv/bin/python3 firmware/check_hardware.py input

Check the output

    ./venv/bin/python3 firmware/check_hardware.py output

Check the status

    ./venv/bin/python3 firmware/check_hardware.py status


# Wiring

[KiCad project](./connections)

![Wiring schema](./docs/connections-schema.png)

![Example wiring](./docs/connections-physical.jpg)

