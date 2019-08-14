
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

After that SSH config is setup. An Example can be found in [./ssh_config](./ssh_config)

    ..

Check connecting via gateway

    ssh door98.dlock.trygvis.io

Update the firmware. See [../ansible/README.md]

    ..

Add to gateway configuration 

    TODO: link to gateway doc

## Debugging gateway connection

If unable to connect to a powered device via the gateway using SSH,
it might be due to a stale SSH tunnel.
This often manifests by SSH client connection hanging forever on new connect.
This can be fixed by doing the following:

List existing SSH tunnel connections. Should be one line per connected device

    netstat -lntp4 | grep :20

Find `sshd` process with the port in question

    sudo lsof -i :20$SERIALNUMBER

Kill the offending SSH process

    sudo kill -9 1111111111111

