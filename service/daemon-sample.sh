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
	kill $PID5
	>&2 echo Teardown complete
	exit 0
}

#register signal handler
trap 'term' INT
trap 'term' QUIT

#move to working directory
cd $LOCATION
cd scripts

#start capturing packets
./capture.py &
PID3=$!
>&2 echo Started capture with PID $PID3

#start categorising packets
sudo -u $USER ./loop.py &
PID4=$!
>&2 echo Started categorisation with PID $PID4

#start the API
sudo -u $USER ./api.py &
PID5=$!
>&2 echo Started the API with PID $PID5

#start angular
cd ../ui
sudo -u $USER ng serve &
PID1=$!
>&2 echo Started angular with PID $PID1

#sleep until sent a SIGINT or SIGTERM
while [ 1 ]; do
	sleep 60
done
