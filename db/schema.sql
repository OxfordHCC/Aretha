--categories table matches readable descriptions to bursts of traffic ("this burst is a weather info request")
drop table if exists categories;
create table categories (
	id integer unsigned auto_increment primary key,
	name varchar(20) not null -- e.g. "Alexa-time" or "Alexa-joke"
);

--collates bursts of traffic and optionally assigns them a category
drop table if exists bursts;
create table bursts (
	id integer unsigned auto_increment primary key,
	category integer references categories --primary key assumed when no column given
);

--store core packet info, and optionally which burst it is part ofi, and which company it represents
drop table if exists packets;
create table packets (
	id integer unsigned auto_increment primary key,
	time datetime not null,
	internal varchar(15) not null, --ip address of local host
	external varchar(15) not null, --ip address of remote host
	len integer not null, --packet length in bytes
	burst integer references bursts, --optional, 
	company integer references companies --optional, assumes table of companies (stolen from refine)
);
