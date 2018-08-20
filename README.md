# IoT-refine Static Interface
Refine for the smart home

A video explaining some features of the UI is below, it is in better quality (mp4) in `/screenGrabs/`:

![IoT Refine Showcase](screenGrabs/IoTRefineShowcase.gif?raw=true "IoT Refine Showcase")

The Static-Refine version is hosted at: https://dkarandikar.github.io/StaticRefine/

How to get this running from scratch:

1. Ensure postgres is installed, create a db with name static, user is postgres and password is password

2. Run `npm install` in /ui and /crunchbaseSupport, also do `npm install @angular/cli@1.1.3` in /ui

3. Run `node google-serv.js` in /crunchbaseSupport

4. Run `ng serve` in \ui and head to `localhost:4200`

To add your own data: 

1. Fill a folder `staticData/` with pcaps labeled by device 

2. Add device Mac and IP to the dictionary in `/categorisation/getAndStoreStaticData.py` with the name in the filename as key

3. Run `/categorisation/getAndStoreStaticData.py`

4. If device names have "unknown" in them, follow directions below 

To add data to existing data:

1. Fill a folder `staticData/` with pcaps labeled by device 

2. Add device Mac and IP to the dictionary in `/categorisation/getAndStoreStaticData.py` with the name in the filename as key

3. Run `/categorisation/getAndStoreStaticData.py [FILE]` where `[FILE]` is the name of the file to be added to the other data 


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

