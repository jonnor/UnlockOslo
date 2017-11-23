# Firmware setup

For Raspberry PI (3), using Raspbian Stretch

### Install apt packages

python3 git

### Setup dedicated user

`dlock`
create homedir,
no login,
add to `gpio` group

### Setup firmware

git clone https://github.com/jonnor/unlockoslo

### Install systemd .service file

```
dlock-firmware
```

systemctl enable dlock-firmware

### Install SSH call-home

TODO: document
