# Production service setup
Manual install for now, can be converted to Ansible playbook or Docker images later.

Debian Stable, 9.2 Stretch

## Install APT packages

```
mosquitto python3-pip git
certbot python-certbot-nginx
nginx
```

### Create dedicated user for service
dlock

Create homedir. No login, no groups

### Install service code

```
git clone https://github.com/jonnor/dlock-oslo.git
pip3 install --user -r firmware/requirements.txt
pip3 install --user -r gateway/requirements.txt
```

### Add config files
Files in this folder

Managed by ansible:

```
cp dlock-mosquitto.conf /etc/mosquitto/conf.d/
cp dlock.trygvis.io /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/dlock.trygvis.io /etc/nginx/sites-enabled/
```

### Add systemd units
Files in this folder

```
dlock-gateway.service
dlock-testdevices.service
mosquitto.service
```

daemon-reload and systemctl enable ....

### Generate SSL certs

`certbot --nginx`

### Allow Mosquitto to read Lets Encrypt certs


Managed by Ansible
```
chown -R mosquitto:root /etc/letsencrypt/live/dlock.trygvis.io
chown -R mosquitto:root /etc/letsencrypt/archive/dlock.trygvis.io
chmod 0755 /etc/letsencrypt/{archive,live}
```

### TODO: SSH config for call-home
