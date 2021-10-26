#! /bin/bash

LOCATION=/home/hcc/IoT-refine/scripts/
USER=hcc

cd $LOCATION
echo Service down...
service iotrefine stop
sleep 1
echo Service up...
service iotrefine start
echo Waiting for everything to start...
sleep 30
sudo -u $USER nohup ./reset-browser.sh
