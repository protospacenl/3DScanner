#!/bin/bash

ON=1

if [ ! -z "$1" ]
then
	ON=$1
fi

echo gpio | sudo tee /sys/class/leds/led0/trigger
echo ${ON} | sudo tee /sys/class/leds/led0/brightness
