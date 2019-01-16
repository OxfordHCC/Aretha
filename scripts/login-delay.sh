#! /bin/sh

LOCATION=/home/mcnutty/Documents/IoT-refine/scripts/

cd $LOCATION
./reset-database.py
echo Waiting for service to come up...
sleep 15
chromium --start-fullscreen --app=http://localhost:4200 http://localhost:4200
