
# Table of Contents

1.  [Install](#org2f95bbd)
2.  [Sudo (USB mount / unmount / `blkid`, system time)](#orgab211fe)
3.  [Run (from repo root)](#orgd0de730)



<a id="org2f95bbd"></a>

# Install

    cd ~/ieos
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r gui/requirements.txt
    pip install -r ieos/requirements.txt


<a id="orgab211fe"></a>

# Sudo (USB mount / unmount / `blkid`, system time)

Run once after clone so the app can use `sudo -n` without a password prompt:

    cd ~/ieos
    sudo bash scripts/pi-sudo-setup.sh


<a id="orgd0de730"></a>

# Run (from repo root)

    cd ~/ieos
    ./ie.sh

