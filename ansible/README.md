
# Deploy firmware update

    ansible-playbook firmware.yml -l dlock-0

# Initialize a new firmware device

    ansible-playbook bootstrap.yml --extra-vars "hosts=dlock-99.local user=trygvis"

# Deploy firmware update

    ansible-playbook dlock.yml
