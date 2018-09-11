#!/bin/bash

CAMERA=
IDENTITY=
IP_BASE=100

usage() { echo "Usage: $0 -c <camera> [-i <identity file>]" 1>&2; exit 1; }

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

if [ -z "${CAMERA}" ]; then
	usage
fi

IP_END=$((CAMERA+IP_BASE))
IP=192.168.2.${IP_END}

echo "Identify camera ${CAMERA} @${IP}"
ssh ${IDENTITY} pi@${IP} << EOF
echo heartbeat | sudo tee /sys/class/leds/led1/trigger;
EOF