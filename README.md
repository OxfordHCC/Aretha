# IoT Refine: X-ray vision for the smart home
Have you ever wondered which companies your smart devices were talking to? Or how much data they send and how often?

IoT Refine captures meta data about the network traffic of devices connected to it. Run IoT Refine on a device with a WiFi hotspot and connect your devices - you might be surprised about what you see.

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

### /api/impacts/\<start>\<end>\<interval>
\<start> and \<end> are Unix timestamps (minimim 0 maximum now)

\<interval> is the interval in minutes that impacts will be grouped into (minimum 1)

Returns the amount of traffic (impact) sent and received between device/ip pairs between \<start> and \<end>. These are aggregated into \<interval> minute intervals. Also returns data about known devices and companies (identical to the devices and geodata endpoints).

### /api/stream
Event stream of new data about companies, devices, and impacts. Companies and devices are sent on discovery, impacts are aggregated and sent every minute.

### /api/geodata
List the name, ip, country code, country name, latitude, and longitude of all companies that have sent or received traffic through IoT Refine.

### /api/devices
List the names, MAC addresses, and nicknames of all local devices that have sent traffic through IoT Refine.

### /api/devices/set/\<mac>/\<nickname>
Set the nickname of device with MAC address \<mac> to \<nickname>.

### /api/aretha/counterexample/\<q>
Provide a counter example to one of the standard Aretha questions (see Aretha project for more information).

### /api/aretha/enforce/\<company>[/\<mac>]
Block network traffic from or to any IP addresses owned by \<company>. By default, this applies to all devices connected to IoT-Refine. To only block traffic from a single local device, supply the device's MAC address in the \<mac> field.

### /api/aretha/unenforce/\<company>[/\<mac>]
Unblock network traffic from or to any IP addresses owned by \<company>. By default, this applies to blocks placed on all traffic only. To unblock traffic from a single local device, supply the device's MAC address in the \<mac> field.
