#! /bin/sh

LOCATION=insert_path_to_ioterfine
USER=user_to_run_as

#define signal handler
term()
{
	>&2 echo Begin teardown
	kill $PID1
	kill $PID2
	kill $PID3
	kill $PID4
	>&2 echo Teardown complete
	exit 0
}

#register signal handler
trap 'term' INT
trap 'term' QUIT

#move to working directory and update
cd $LOCATION
git pull
cd scripts

#start the wifi hotspot
./reset-wifi.sh

#start capturing packets
./capture.py &
PID1=$!
>&2 echo Started capture with PID $PID1

#start categorising packets
sudo -u $USER ./loop.py &
PID2=$!
>&2 echo Started categorisation with PID $PID2

#start the API
sudo -u $USER gunicorn --bind 127.0.0.1:4201 --workers 2 --threads 4 --timeout 30 api:app
PID3=$!
>&2 echo Started the API with PID $PID3

#start angular
cd ../ui
sudo -u $USER ng serve &
PID4=$!
>&2 echo Started angular with PID $PID4

#sleep until sent a SIGINT or SIGTERM
while [ 1 ]; do
	sleep 60
done
