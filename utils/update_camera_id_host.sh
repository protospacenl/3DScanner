#!/bin/bash

IP=$1
ID=$2

ssh -i identity pi@192.168.2.${IP} << EOF
cd 3DScanner/firmware;
sudo ./update_camera_id.sh ${ID};
sudo reboot;
EOF
