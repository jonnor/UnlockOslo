
### SSH reverse proxy

The RPI firmware units are set up to establish a reverse SSH tunnel to the gateway machine.
This lets one connect even if the firmware devices are not directly reachable on the internet,
ie behind NAT on 4G or WiFi/Ethernet. 

One can connect via the gateway as 'jumphost' by adding a SSH config like:
```
Host dlock-2
 	User username
	ProxyCommand=ssh dlock-gateway nc localhost 2002
```

Then
```
ssh -t dlock-2 bash
```
