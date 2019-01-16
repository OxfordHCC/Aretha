#! /bin/sh

echo Starting IoT-refine
echo Waiting for service to come up...
sleep 15
chromium --start-fullscreen --app=http://localhost:4200 http://localhost:4200
