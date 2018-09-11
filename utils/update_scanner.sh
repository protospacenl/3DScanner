#!/bin/bash

IP_BASE=192.168.2
IP_END=100
IDENTITY=
CAMERA=`echo {1..30}`

usage() { echo "Usage: $0 [-c <camera>] [-i <identity file>]" 1>&2; exit 1; }

while getopts ":c:i:" o; do
    case "${o}" in
        c)
            CAMERA=${OPTARG}
            ;;
        i)
            IDENTITY="-i ${OPTARG}"
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

for i in $CAMERA; do
	NEW_END=$((i+IP_END))
	IP=${IP_BASE}.${NEW_END}
	echo "Updating ${i} -> ${IP}"
	
	scp ${IDENTITY} ../firmware/client/Client.py pi@${IP}:3DScanner/firmware/client/
	./identify_camera.sh ${IDENTITY} -c $i
	
done
