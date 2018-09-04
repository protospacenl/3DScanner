#!/bin/bash

IP=$1

ssh -i identity pi@192.168.2.${IP} << EOF
sudo 3DScanner/firmware/remove_vnc.sh;
echo heartbeat | sudo tee /sys/class/leds/led0/trigger;
echo heartbeat | sudo tee /sys/class/leds/led1/trigger;
EOF