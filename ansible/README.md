
# Developer machine setup

## Vault password

Should be added as `.vault_pass` in project toplevel.

## SSH config to reach devices

The firmware units establish a reverse SSH tunnel to the gateway machine.
This lets one connect even if the firmware devices are not directly reachable on the internet,
ie behind NAT on 4G or WiFi/Ethernet. 

One can connect via the gateway as 'jumphost' by adding a SSH config like:
```
Host door1.dlock.trygvis.io
 	User USERNAME
	ProxyCommand=ssh dlock.trygvis.io nc localhost 2001
```
Where 2001 is 2000+$devicenumber

Then test it using 
```
ssh -t door2.dlock.trygvis.io bash
```

# Common tasks

## Deploy firmware to devices

    ansible-playbook firmware.yml -l dlock-0

## Deploy gateway update

    # FIXME: not entirely automated yet
    ansible-playbook gateway.yml

## Initialize a new firmware device

    ansible-playbook bootstrap.yml --extra-vars "hosts=dlock-99.local user=trygvis"

## Certbot

    certbot register --agree-tos
    certbot certonly -d $DOMAIN --webroot /var/www/html
