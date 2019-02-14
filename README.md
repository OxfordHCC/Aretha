# IoT-refine
Refine for the smart home

A video explaining some features of the UI is below, it is in better quality (mp4) in `/screenGrabs/`:

![IoT Refine Showcase](screenGrabs/IoTRefineShowcase.gif?raw=true "IoT Refine Showcase")

A static version of IoT Refine is hosted at: https://dkarandikar.github.io/StaticRefine/

## Install
1. Ensure postgres is installed, create a db with name testdb, user is postgres and password is password

2. Install python3 dependencies: `pip3 install psycopg2-binary pandas sklearn Pyshark flask gunicorn`

3. Install angular (for Refine web interface): `cd ui/ && npm install && npm install -g @angular/cli`

4. Install the wireshark command line tools (tshark) `pacman -S wireshark-cli` (or equivalent for your platform)

5. Configure the database from the schema: `/scripts/reset-database.py` (dbname=`testdb` user=`postgres` password=`password`)

6. Copy `config-sample.cfg` to `config.cfg` and change values as appropriate

## Run (manually)
1. Run `ng serve` in \ui

2. Run `scripts/capture.py`, `/scripts/loop.py` and `gunicorn --bind 127.0.0.1:4201 api:app`

3. The web front end will be available at `localhost:4200`, and the API at `localhost:4201`

## Run (systemd service)

1. Copy `service/iotrefine-sample.service` to `/etc/systemd/system/iotrefine.service` and edit in the marked fields

2. Copy `service/daemon-sample.sh` to `service/daemon.sh` and edit the marked fields

2. Start and stop the service by running `sudo systemctl {start|stop} iotrefine`

3. Enable or disable IoT Refine on boot by running `sudo systemctl {enable|disable} iotrefine`

4. To have chromium point at iotrefine on login, copy and fill out logintask-sample.desktop and move it to ~/.config/autostart/

## Configure Device Names

Device names will initially display as MAC addresses. To assign a 'friendly' name to a device, use the `SetDevice` API endpoint:

`localhost:4201/api/setdevice/aa:bb:cc:dd:ee:ff/Alice iPhone`

## Reset the database
Run `scripts/reset-database.py`

## Companion Amazon Alexa Skill
Work in progress. Skill files are stored in the `ask` directory
