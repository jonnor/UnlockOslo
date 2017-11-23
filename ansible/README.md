# Ansible basics

## Bootstrapping a new host

    ansible-playbook ../bootstrap.yml --extra-vars "hosts=dlock user=trygvis"

## Executing the playbook

We have a ansible repository per host for now. To run the playbook
from your local machine:

    ansible-playbook dlock.yml
