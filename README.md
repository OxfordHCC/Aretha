# IoT-refine
Refine for the smart home

How to get this running from scratch:

1. Ensure postgres is installed, create a db with name testdb, user is postgres and password is password

2. Install the following python packages: `psycopg2 scapy pandas sklearn ipdata Pyshark`

2. Run `npm install` in /ui and /crunchbaseSupport, also do `npm install @angular/cli@1.1.3` in /ui

3. Run `/capture/resetDb.py` and then `/db/runRefine.py`

4. Run `node google-serv.js` in /crunchbaseSupport

5. Run `ng serve` in \ui and head to `localhost:4200`

6. Run`/capture/capture.py` and `/categorisation/loop.py` to capture data and it should display in this browser 

7. Optionally install the systemd service by copying iotrefine.service to `/etc/systemd/system/`. You can start/stop it by running `sudo systemctl {start|stop} iotrefine` and have it start on boot by running `sudo systemctl enable iotrefine`

A video explaining some features of the UI is below, it is in better quality (mp4) in `/screenGrabs/`:

![IoT Refine Showcase](screenGrabs/IoTRefineShowcase.gif?raw=true "IoT Refine Showcase")

## Device names

A lot of the device names will initially show up as Unknown, this is because the user must manually relate manufacturers, which are obtained from mac addresses, to devices they own

To do this, one must navigate to `\ui\src\assets\data\iotData.json` and edit the dictionary called manDev to change devices from Unknown to whatever one actually owns 

Then, to show this in the UI, run `/db/runRefine.py True`

You may then need to refresh the browser to display the updated data 

## Db

Written for Postgres

Nice things:
* When looking for packets to bin into bursts, can just look for packets where (burst == NULL)
* Ditto for bursts to categories

To reset the capture data and db:
run `resetDb.py` and `runRefine.py`

## UI

Stripped away a lot of the components from other views that we don't want/need for IoT-refine

Not using an API for the db instead outputting to json

## UI scratch

A misguided attempt to build the UI from scratch, hacking refine will be far uglier code but will have far more features if it works 

Pip install dnspython and ipwhois, run `dbTocsv.py` to convert postgres data to csv, visualise with stacked bars in `test.html`

## Testing

Create a postgres db with name testdb, user is postgres and password is password (or else change in `databaseBursts.py`)

Run `testDB.py` to populate with packet data from `AlexaTime1`

Run `testCategorisation.py` to run categorisation scripts on this data

Expected result is 3 bursts, all of which are Time.
Output should be similar to [(1, 1), (2, 1), (3, 1)], [(1, 'Time')]. 

Run `/db/runRefine.py True` to then populate this data into the UI 
