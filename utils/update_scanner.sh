#!/bin/bash

IP_BASE=192.168.2
IP_END=100

for i in {1..30}; do
	NEW_END=$((i+IP_END))
	IP=${IP_BASE}.${NEW_END}
	echo "Updating ${i} -> ${IP}"
	scp -i identity ../firmware/client/Client.py pi@${IP}:3DScanner/firmware/client/
	./identify_camera.sh $i
done
