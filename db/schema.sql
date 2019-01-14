--categories table matches readable descriptions to bursts of traffic ("this burst is a weather info request")
drop table if exists categories cascade ;
create table categories (
	id SERIAL primary key,
	name varchar(40) not null -- e.g. "Alexa-time" or "Alexa-joke"
);

--collates bursts of traffic and optionally assigns them a category
drop table if exists bursts cascade ;
create table bursts (
	id SERIAL primary key,
	category integer references categories --primary key assumed when no column given
);

--store core packet info, and optionally which burst it is part ofi, and which company it represents
drop table if exists packets cascade ;
create table packets (
	id SERIAL primary key,
	time timestamp not null,
	src varchar(15) not null, --ip address of sending host
	dst varchar(15) not null, --ip address of receiving host
	mac varchar(17) not null, --mac address of internal host
	len integer not null, --packet length in bytes
	proto varchar(10) not null, --protocol if known, otherwise port number
	burst integer references bursts --optional,
	--company integer references companies --optional, assumes table of companies (stolen from refine)
);

-- create two indexes on src and dst to speed up lookups by these cols by loop.py
create index on packets (src);
create index on packets (dst);

drop table if exists devices cascade;
create table devices(
	mac varchar(17) primary key,
	manufacturer varchar(40),
	name varchar(40) DEFAULT 'unknown'
);

drop table if exists geodata cascade;
create table geodata(
	ip varchar(15) primary key,
	lat real not null,
	lon real not null,
	c_code varchar(2) not null,
	c_name varchar(20) not null
);

--store simplified profiles of devices: Name, time, destination company, traffic
drop table if exists models cascade ;
create table models (
	id SERIAL primary key,
	device varchar(17) not null, --device mac address
	time timestamp not null, --time the model was made
	destination varchar(20) not null, --name of the company data was sent to
	location varchar(2) not null, --country the company is based in
	impact real not null --amount of traffic in mb
);
