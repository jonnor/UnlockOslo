
[Code](./dlockoslo.py)

[Tests](./test_doorsystem.py)

## Setting up new device

Flash base image

    gunzip -c dlock-firmware-base.tgz | sudo dd of=/dev/MYSCARD status=progress oflag=sync bs=1M

Mount image

    TODO

Determine device name

    Devices are named dlock-$ID, where $ID is incremented by 1 for each new device
    No leading zeroes!
    Example: dlock-98 

Set hostname to device name

    # Edit /etc/hostname to be dlock-98
    # Edit /etc/hosts

Boot the device

    Insert SDcard into Raspberry PI
    Plug in Ethernet cable
    Plug in USB power
    
Check that one can connect directly

    ssh dlock-98.local

Check connecting via gateway

    TODO: link to SSH config
    ssh door98.dlock.trygvis.io

Update the firmware

    TODO: link to Ansible

Add to gateway configuration 

    TODO: link to gateway doc
