
# Table of Contents

1.  [Prerequisites](#org70cde3f)
2.  [Install](#org17036f6)
3.  [Sudo (USB mount / unmount / `blkid`, system time)](#org014d976)
4.  [Run (from repo root)](#org2de1e26)



<a id="org70cde3f"></a>

# Prerequisites

Clone the repository (e.g. to `~/ieos`). Enable SPI for the OLED: `sudo raspi-config` → Interface Options → SPI → Yes; reboot if prompted.

Run the bootstrap script as your normal login user (not root).


<a id="org17036f6"></a>

# Install

    cd ~/ieos
    bash scripts/pi-bootstrap.sh


<a id="org014d976"></a>

# Sudo (USB mount / unmount / `blkid`, system time)

Run once after clone so the app can use `sudo -n` without a password prompt:

    cd ~/ieos
    sudo bash scripts/pi-sudo-setup.sh


<a id="org2de1e26"></a>

# Run (from repo root)

    cd ~/ieos
    ./ie.sh

