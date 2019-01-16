#! /bin/bash

LOCATION=/home/mcnutty/Documents/IoT-refine/scripts/

cd $LOCATION
service iotrefine stop
sleep 1
./reset-database.py
sleep 1
service iotrefine start
sleep 20
./reset-browser.sh
