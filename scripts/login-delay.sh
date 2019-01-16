#! /bin/sh

LOCATION=/home/mcnutty/Documents/IoT-refine/scripts/

echo Starting IoT-refine\n
echo Clearing database...
cd $LOCATION
./reset-database.sh

echo Waiting for service to come up...
sleep 15
chromium --start-fullscreen --app=http://localhost:4200 http://localhost:4200
