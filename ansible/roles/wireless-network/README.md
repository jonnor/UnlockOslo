You will need to define

 wifi_ssid: <ssid>
 wifi_psk: <psk>

in a file ../../host_vars/<hostname>/wifi.yml

and encrypt it with ansible-vault before this role will work. NOTE: remember to encrypt before the file leaves your machine!
