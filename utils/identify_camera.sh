#!/bin/bash

ID=$1
IP_BASE=100

IP_END=$((ID+IP_BASE))
IP=192.168.2.${IP_END}

ssh -i identity pi@${IP} << EOF
echo heartbeat | sudo tee /sys/class/leds/led1/trigger;
EOF