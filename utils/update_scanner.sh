#!/bin/bash

MOUNTPOINT=/mnt

if [[ -b $1 ]]
then
    mount $1 $MOUNTPOINT
    echo "MOUNTED on $MOUNTPOINT"

    rm -rf $MOUNTPOINT/home/pi/3DScanner
    cp -rv ../../3DScanner $MOUNTPOINT/home/pi/3DScanner/
    cp -v ../firmware/fs/*.service $MOUNTPOINT/etc/systemd/system/
    chmod -x $MOUNTPOINT/etc/systemd/system/3dscanner.service
    umount /mnt
else
    echo "FAILED"
fi
