#! /bin/bash

LOCATION=/home/mcnutty/Documents/IoT-refine/scripts/

cd $LOCATION
echo Service down...
service iotrefine stop
sleep 1
./reset-database.py
sleep 1
echo Service up...
service iotrefine start
echo Waiting for everything to start...
sleep 20
env DISPLAY=0.0 ./reset-browser.sh
