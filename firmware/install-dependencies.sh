#!/bin/bash

sudo apt-get install -y python-setuptools python-pip
sudo apt-get install -y realvnc-vnc-server

pip install -r client/requirements.txt
