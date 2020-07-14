This (minimal) role configures ntp servers for a dlock host. Useful if the host cannot reach public ntp servers.

Define ntp_servers in ../../host_vars/<hostname>/ntp.yml with hostnames or ip adresses.

Example:

```
ntp_servers:
  - 0.pool.ntp.org
  - 1.pool.ntp.org
  - 2.pool.ntp.org
  - 3.pool.ntp.org
```