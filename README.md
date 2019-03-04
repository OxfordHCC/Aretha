# IoT-refine
Refine for the smart home

A video explaining some features of the UI is below, it is in better quality (mp4) in `/screenGrabs/`:

![IoT Refine Showcase](screenGrabs/IoTRefineShowcase.gif?raw=true "IoT Refine Showcase")

A static version of IoT Refine is hosted at: https://dkarandikar.github.io/StaticRefine/

## Install
1. Install package dependcies: PostgreSQL, NodeJS, Node Package Manager (npm), Python3, Wireshark CLI (sometimes called tshark)

2. Install python3 dependencies: `pip3 install psycopg2-binary pandas sklearn Pyshark flask gunicorn`

3. Install NodeJS dependency angular: `cd ui/ && npm install && npm install -g @angular/cli`

4. Copy `config-sample.cfg` to `config.cfg` and add values for at least [ipdata][key], [postgres][database], [postgres[username], and [postgres][password]

5. Configure the database from the schema: `/scripts/reset-database.py`

6. If you are using iptables-based functionality (`/api/aretha/enforce`), ensure that iptables rules will persist across reboots (e.g. by installing the iptables-persistent package on debian), and that the user running IoT-Refine is able to run iptables as root without a password

## Run (manually)
1. In `/ui` run `ng serve`

2. In `/scripts` run `capture.py`, `loop.py` and `gunicorn --bind 127.0.0.1:4201 -w2 -t4 --timeout 300 api:app`

3. The web front end will be available at `localhost:4200`, and the API at `localhost:4201`

## Run (systemd service)

1. Copy `service/iotrefine-sample.service` to `/etc/systemd/system/iotrefine.service` and edit in the marked fields

2. Copy `service/daemon-sample.sh` to `service/daemon.sh` and edit the marked fields

2. Start and stop the service by running `sudo systemctl {start|stop} iotrefine`

3. Enable or disable IoT Refine on boot by running `sudo systemctl {enable|disable} iotrefine`

4. To have chromium point at iotrefine on login, copy and fill out logintask-sample.desktop and move it to ~/.config/autostart/

## Reset the Database
Run `scripts/reset-database.py`

## API Endpoints

### /api/refine/\<n>
Entry point for the refine web interface. Returns information on network flows to and from all devices in the last \<n> minutes.

### /api/devices
List the names and MAC addresses of all local devices that have sent traffic through IoT-Refine.

### /api/devices/set/\<mac>/\<name>
Set the name of device with MAC address \<mac> to \<name>.

### /api/aretha/counterexample/\<q>
Provide a counter example to one of the standard Aretha questions (see Aretha project for more information).

### /api/aretha/enforce/\<company>[/\<mac>]
Block network traffic from or to any IP addresses owned by \<company>. By default, this applies to all devices connected to IoT-Refine. To only block traffic from a single local device, supply the device's MAC address in the \<mac> field.

### /api/aretha/unenforce/\<company>[/\<mac>]
Unblock network traffic from or to any IP addresses owned by \<company>. By default, this applies to blocks placed on all traffic only. To unblock traffic from a single local device, supply the device's MAC address in the \<mac> field.

### /stream
Event stream of updates to the database. Used to refresh the refine web interface.
