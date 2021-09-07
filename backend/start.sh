#! /bin/bash

# exit when any command fails
set -e

#start the wifi hotspot
#./reset-wifi.sh

#start capturing packets
python -m capture &
PID_CAPTURE=$!

#start categorising packets
python -m loop &
PID_LOOP=$!

#start the API
python -m api &
PID_API=$!


wait $PID_CAPTURE
wait $PID_LOOP
wait $PID_API

#sleep until sent a SIGINT or SIGTERM
while [ 1 ]; do
	sleep 60
done
