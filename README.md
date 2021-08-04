# Aretha: X-ray vision for the smart home
Have you ever wondered which companies your smart devices were talking to? Or how much data they send and how often?

Aretha captures meta data about the network traffic of devices connected to it. Run Aretha on a device with a WiFi hotspot and connect your devices - you might be surprised about what you see.


# Database
You can either start a database using docker, or manually using a Postgres install.

## Using Docker
1. Modify docker-compose.yaml with preferred db settings
You can also leave them as is.

2. run docker-compose up in the root directory
```
$> docker-compose up
```
A postgres db will be started in a container using the config.

## Postgres
1. Install PostgreSQL and start server
2. Create a database and an admin user for the database
3. Init db with sql file in ./db/schema.sql

TODO: more detailed instructions for how to do this

# Backend
0. Copy `config-sample.cfg` to `config.cfg` and add values for at least [ipdata][key], [postgres][database], [postgres[username], and [postgres][password]

The postgres config must match the info used when starting the postgres database.

1. Install tshark (wireshark cli), python3 and pipenv

2. Install packages
```
$> cd backend
$> pipenv sync
```

3. Start shell inside virtual env
```
$> pipenv shell
```

4. Start processing loop
```
$> python -m loop
```

5. Start packet capture loop
```
$> python -m capture
```

6. Start http server for API
```
$> python -m api
```

# User Interface
1. Install Node and npm.
2. Install npm packages
```
$> cd ui
$> npm install
```

3. Start http server using angular cli
```
$> npx ng serve
```

4. Go to localhost:4200 in your browser


# Legacy instructions

##  Run as systemd service
If you are using iptables-based functionality (`/api/aretha/enforce`), ensure that iptables rules will persist across reboots (e.g. by installing the iptables-persistent package on debian), and that the user running Aretha is able to run iptables as root without a password

1. Copy `service/iotrefine-sample.service` to `/etc/systemd/system/iotrefine.service` and edit in the marked fields

2. Copy `service/daemon-sample.sh` to `service/daemon.sh` and edit the marked fields

2. Start and stop the service by running `sudo systemctl {start|stop} iotrefine`

3. Enable or disable Aretha on boot by running `sudo systemctl {enable|disable} iotrefine`

4. To have chromium point at Aretha on login, copy and fill out logintask-sample.desktop and move it to ~/.config/autostart/

##  Reset the Database
Run `scripts/reset-database.py`

# API Endpoints

### /api/impacts/\<start>\<end>\<interval>
\<start> and \<end> are Unix timestamps (minimim 0 maximum now)

\<interval> is the interval in minutes that impacts will be grouped into (minimum 1)

Returns the amount of traffic (impact) sent and received between device/ip pairs between \<start> and \<end>. These are aggregated into \<interval> minute intervals. Also returns data about known devices and companies (identical to the devices and geodata endpoints).

### /api/stream
Event stream of new data about companies, devices, and impacts. Companies and devices are sent on discovery, impacts are aggregated and sent every minute.

### /api/geodata
List the name, ip, country code, country name, latitude, and longitude of all companies that have sent or received traffic through Aretha.

### /api/devices
List the names, MAC addresses, and nicknames of all local devices that have sent traffic through Aretha.

### /api/devices/set/\<mac>/\<nickname>
Set the nickname of device with MAC address \<mac> to \<nickname>.

### /api/aretha/counterexample/\<q>
Provide a counter example to one of the standard Aretha questions (see Aretha project for more information).

### /api/aretha/enforce/\<company>[/\<mac>]
Block network traffic from or to any IP addresses owned by \<company>. By default, this applies to all devices connected to Aretha. To only block traffic from a single local device, supply the device's MAC address in the \<mac> field.

### /api/aretha/unenforce/\<company>[/\<mac>]
Unblock network traffic from or to any IP addresses owned by \<company>. By default, this applies to blocks placed on all traffic only. To unblock traffic from a single local device, supply the device's MAC address in the \<mac> field.
