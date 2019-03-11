#! /bin/bash

LOCATION=/home/mcnutty/Documents/IoT-refine/scripts/
USER=mcnutty

cd $LOCATION
echo Service down...
service iotrefine stop
sleep 1
sudo -u $USER ./reset-database.py
sleep 1
echo Service up...
service iotrefine start
echo Waiting for everything to start...
sleep 20
sudo -u $USER nohup ./reset-browser.sh
