After dist-upgrade and necessary reboots on 2021-04-14, the ssh host keys on the gateway changed.

Metadata
```
root@dlock-prod:~# who -b
         system boot  2021-04-14 11:16

root@dlock-prod:~# ls -la /etc/ssh
total 584
drwxr-xr-x  2 root root   4096 Apr 14 10:51 .
drwxr-xr-x 93 root root   4096 Apr 15 11:23 ..
-rw-r--r--  1 root root 553122 Mar  1  2019 moduli
-rw-r--r--  1 root root   1723 Mar  1  2019 ssh_config
-rw-r--r--  1 root root   3280 May 14  2019 sshd_config
-rw-------  1 root root    227 Apr 14 10:51 ssh_host_ecdsa_key
-rw-r--r--  1 root root    177 Apr 14 10:51 ssh_host_ecdsa_key.pub
-rw-------  1 root root    411 Apr 14 10:51 ssh_host_ed25519_key
-rw-r--r--  1 root root     97 Apr 14 10:51 ssh_host_ed25519_key.pub
-rw-------  1 root root   1679 Apr 14 10:51 ssh_host_rsa_key
-rw-r--r--  1 root root    397 Apr 14 10:51 ssh_host_rsa_key.pub

root@dlock-prod:~# ls -la --time-style=full-iso /etc/ssh
total 584
drwxr-xr-x  2 root root   4096 2021-04-14 10:51:32.962229000 +0200 .
drwxr-xr-x 93 root root   4096 2021-04-15 12:12:51.955552652 +0200 ..
-rw-r--r--  1 root root 553122 2019-03-01 17:19:28.000000000 +0100 moduli
-rw-r--r--  1 root root   1723 2019-03-01 17:19:28.000000000 +0100 ssh_config
-rw-r--r--  1 root root   3280 2019-05-14 23:35:07.069138745 +0200 sshd_config
-rw-------  1 root root    227 2021-04-14 10:51:32.962229000 +0200 ssh_host_ecdsa_key
-rw-r--r--  1 root root    177 2021-04-14 10:51:32.962229000 +0200 ssh_host_ecdsa_key.pub
-rw-------  1 root root    411 2021-04-14 10:51:32.870229000 +0200 ssh_host_ed25519_key
-rw-r--r--  1 root root     97 2021-04-14 10:51:32.870229000 +0200 ssh_host_ed25519_key.pub
-rw-------  1 root root   1679 2021-04-14 10:51:32.802229000 +0200 ssh_host_rsa_key
-rw-r--r--  1 root root    397 2021-04-14 10:51:32.802229000 +0200 ssh_host_rsa_key.pub
```

and etckeeper doesn't show anything unusual

```
root@dlock-prod:/etc/ssh# etckeeper vcs status
On branch master
nothing to commit, working tree clean

root@dlock-prod:/etc/ssh# etckeeper vcs diff
```

I used ansible ad-hoc commands to fetch the files from the server, like so:

`ansible dlock-gcp -m fetch -a 'src=/etc/ssh/ssh_host_ecdsa_key dest=../backup/gw_20210415/ flat=yes' --become`

the files were then encrypted with ansible-vault