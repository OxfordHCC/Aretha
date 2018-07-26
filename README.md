# IoT-refine Static Interface
Refine for the smart home

How to get this running from scratch:

1. Ensure postgres is installed, create a db with name static, user is postgres and password is password

2. Run `npm install` in /ui and /crunchbaseSupport, also do `npm install @angular/cli@1.1.3` in /ui

3. Run `/capture/resetDb.py` and then `/db/runRefine.py`

4. Run `node google-serv.js` in /crunchbaseSupport

5. Run `ng serve` in \ui and head to `localhost:4200`

6. Run`capture.py` to capture data and it should display in this browser 

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

Run `testDB.py` to populate with packet data from `AlexaTest1`

Run `testCategorisation.py` to run categorisation scripts on this data

Expected result is 8 bursts, 3 of which are Time and the rest are Unknown. 
Output should be similar to [(1, 1), (2, 2), (3, 2), (4, 2), (5, 1), (6, 2), (7, 2), (8, 1)]