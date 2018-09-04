#!/bin/bash

ID=$1
IP_BASE=192.168.2
IP_END=100

usage() {
	echo "Usage: ${0} [id]"
}

if [ -z "${ID}" ]; then
	usage
	exit 1
fi

echo ${ID} > /etc/camera_id
IP_END=$(( $IP_END + $ID ))
IP=${IP_BASE}.${IP_END}

echo "Setting IP addres to: ${IP}"
cat "fs/dhcpcd.conf" | sed -e "s/{CAMERA_IP}/${IP}/" > /etc/dhcpcd.conf

