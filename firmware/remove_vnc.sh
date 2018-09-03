#!/bin/bash

rm -v /etc/systemd/system/default.target
ln -sv /lib/systemd/system/multi-user.target /etc/systemd/system/default.target
rm -v /etc/systemd/system/multi-user.target.wants/vncserver-x11-serviced.service
