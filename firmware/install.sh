#!/bin/bash

sudo install fs/3dscanner.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable 3dscanner.service
