#! /bin/sh

killall chromium #stop currently open browser window(s)
/usr/bin/chromium --start-fullscreen --app=http://localhost:4200 http://localhost:4200 & #open chromium fullscreen on iotrefine
