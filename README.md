# IoT-refine
Refine for the smart home

* db
* (pyshark -> db)
* (db -> bursts -> NN -> db)
* (front end)
* init

## UI

To get the xray UI running do `npm install` in /ui and /crunchbaseSupport, also do `npm install @angular/cli@1.1.3` in /ui

Then run `node google-serv.js` in /crunchbaseSupport

Then run `ng serve` in \ui and head to `localhost:4200`

Stripped away a lot of the components from other views that we don't want/need for IoT-refine

Not using an API for the db instead outputting to json

## UI scratch

A misguided attempt to build the UI from scratch, hacking refine will be far uglier code but will have far more features if it works 

Pip install dnspython and ipwhois, run `dbTocsv.py` to convert postgres data to csv, visualise with stacked bars in `test.html`

## Db

Written for Postgres

Nice things:
* When looking for packets to bin into bursts, can just look for packets where (burst == NULL)
* Ditto for bursts to categories

## Testing

Create a postgres db with name testdb, user is postgres and password is password (or else change in `databaseBursts.py`)

Run `testDB.py` to populate with packet data from `AlexaTest1`

Run `testCategorisation.py` to run categorisation scripts on this data

Expected result is 8 bursts, 3 of which are Time and the rest are Unknown. 
Output should be similar to [(1, 1), (2, 2), (3, 2), (4, 2), (5, 1), (6, 2), (7, 2), (8, 1)]