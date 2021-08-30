#! /bin/bash

#start the wifi hotspot
#./reset-wifi.sh

#start capturing packets
sudo python -m capture &
PID1=$!
>&2 echo Started capture with PID $PID1

#start categorising packets
python -m loop &
PID2=$!
>&2 echo Started categorisation with PID $PID2

#start the API
python -m api &
PID3=$!
>&2 echo Started the API with PID $PID3

#sleep until sent a SIGINT or SIGTERM
while [ 1 ]; do
	sleep 60
done
