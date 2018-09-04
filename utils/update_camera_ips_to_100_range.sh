#!/bin/bash

IP_OLD_BASE=150

for i in {2..30}; do
	IP_END=$((i+IP_OLD_BASE))
	IP=192.168.2.${IP_END}
	echo "Updating ${i} -> ${IP}"
	scp -i identity ../firmware/update_camera_id.sh pi@${IP}:3DScanner/firmware/update_camera_id.sh
	./update_camera_id_host.sh $IP_END $i
	#./identify_camera.sh $i
done