#!/bin/bash

#set -o xtrace

. /ci-scripts/include.sh

apt update -y
apt install -y dh-virtualenv dpkg-dev dh-exec build-essential fakeroot git python3-all \
    dh-python python3-pip python3-dev libffi-dev python3-setuptools python3-venv curl

#PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')

#Pip package metainfo file
#sed -i "s/version=.*/version=\\'${DALI_VERSION}\\',/" setup.py

# change python venv path
#sed -i "s/python3.7/python${PYTHON_VERSION}/g" debian/unipi-dali.service