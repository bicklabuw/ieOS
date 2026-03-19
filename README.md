# InsectEavesdropperDevice
This repository contains only the code used on the Insect Eavesdropper Device

# USB Mount Setup
  1. copy usb-mount.sh to /usr/local/bin/ and make it
  executable:
  sudo cp usb-mount.sh /usr/local/bin/usb-mount.sh
  sudo chmod +x /usr/local/bin/usb-mount.sh

  2. allow the pi user to mount/umount without a password:
  echo 'pi ALL=(root) NOPASSWD: /bin/mount, /bin/umount, /sbin/blkid,
  /usr/bin/mount, /usr/bin/umount, /usr/sbin/blkid' | sudo tee
  /etc/sudoers.d/ieos-mount
  sudo chmod 440 /etc/sudoers.d/ieos-mount

  sudo mkdir -p /mnt/usb0