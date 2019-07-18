--store core packet info, and optionally which burst it is part ofi, and which company it represents
drop table if exists packets cascade;
create table packets (
	id SERIAL primary key,
	time timestamp not null,
	src varchar(45) not null, --ip address of sending host
	dst varchar(45) not null, --ip address of receiving host
	mac varchar(17) not null, --mac address of internal host
	len integer not null, --packet length in bytes
	proto varchar(10) not null, --protocol if known, otherwise port number
	ext varchar(45) not null --external ip address (either src or dst)
);

-- create two indexes on src and dst to speed up lookups by these cols by loop.py
create index on packets (src);
create index on packets (dst);
create index on packets (time);

drop table if exists devices cascade;
create table devices(
	mac varchar(17) primary key,
	manufacturer varchar(40),
	name varchar(255) DEFAULT 'unknown'
);

drop table if exists geodata cascade;
create table geodata(
	ip varchar(45) primary key,
	lat real not null,
	lon real not null,
	c_code varchar(2) not null,
	c_name varchar(25) not null,
	domain varchar(30) not null,
	tracker boolean default false
);

--firewall rules created by aretha
drop table if exists rules cascade;
create table rules(
	id SERIAL primary key,
	device varchar(17), --optional device to block traffic from (otherwise all devices)
	c_name varchar(25) not null --so that other matching ips can be blocked in future
);

--ip addresses blocked by aretha
drop table if exists blocked_ips cascade;
create table blocked_ips(
	id SERIAL primary key,
	ip varchar(45) not null,
	rule integer not null references rules on delete cascade
);

--beacon responses received from deployed research equipment
drop table if exists beacon;
create table beacon(
	id SERIAL primary key,
	source int not null,
	packets integer not null,
	geodata integer not null,
	firewall integer not null,
	time timestamp default timezone('utc', now())
);

--questions to ask during studies
drop table if exists content;
create table content(
	name varchar(20) primary key,
	live timestamp not null,
	complete boolean default false,
	pre varchar(500),
	post varchar(500)
);

--load questions
insert into content(name, live) values
	('S1', '2019-06-01T15:14:00'),
	('S2', '2019-06-01T15:14:00'),
	('S3', '2019-06-01T15:14:00'),
	('B1', '2019-06-01T15:14:00'),
	('B2', '2019-06-01T15:14:00'),
	('B3', '2019-06-01T15:14:00'),
	('B4', '2019-06-01T15:14:00'),
	('D1', '2019-06-01T15:14:00'),
	('D2', '2019-06-01T15:14:00'),
	('D3', '2019-06-01T15:14:00'),
	('D4', '2019-06-01T15:14:00'),
	('SD1', '2019-06-01T15:14:00');

drop table if exists activity;
create table activity(
	id SERIAL primary key,
	time timestamp default timezone('utc', now()),
	pid varchar(5) not null,
	category varchar(50) not null,
	description varchar(50) not null
);

drop materialized view if exists impacts;
create materialized view impacts as
	select mac, ext, round(extract(epoch from time)/60) as mins, sum(len) as impact
	from packets
	group by mac, ext, mins
	order by mins
with data;

drop materialized view if exists impacts_aggregated;
create materialized view impacts_aggregated as
	select mac, ext, sum(len) as impact
	from packets
	group by mac, ext
with data;

drop function if exists notify_trigger();
CREATE FUNCTION notify_trigger() RETURNS trigger AS $trigger$
DECLARE
  rec RECORD;
  payload TEXT;
  column_name TEXT;
  column_value TEXT;
  payload_items JSONB;
BEGIN
  -- Set record row depending on operation
  CASE TG_OP
  WHEN 'INSERT', 'UPDATE' THEN
     rec := NEW;
  WHEN 'DELETE' THEN
     rec := OLD;
  ELSE
     RAISE EXCEPTION 'Unknown TG_OP: "%". Should not occur!', TG_OP;
  END CASE;
  
  -- Get required fields
  FOREACH column_name IN ARRAY TG_ARGV LOOP
    EXECUTE format('SELECT $1.%I::TEXT', column_name)
    INTO column_value
    USING rec;
    payload_items := coalesce(payload_items,'{}')::jsonb || json_build_object(column_name,column_value)::jsonb;
  END LOOP;

  -- Build the payload
  payload := json_build_object(
    'timestamp',timezone('utc', now()),
    'operation',TG_OP,
    'schema',TG_TABLE_SCHEMA,
    'table',TG_TABLE_NAME,
    'data',payload_items
  );

  -- Notify the channel
  PERFORM pg_notify('db_notifications', payload);
  
  RETURN rec;
END;
$trigger$ LANGUAGE plpgsql;

drop trigger if exists packets_notify on packets;
create trigger packets_notify after insert or update or delete on packets
for each row execute procedure notify_trigger(
  'mac',
  'ext',
  'len'
);


drop trigger if exists device_notify on devices;
CREATE TRIGGER device_notify AFTER INSERT OR UPDATE OR DELETE ON devices
FOR EACH ROW EXECUTE PROCEDURE notify_trigger(
  'mac',
  'manufacturer',
  'name'
);

drop trigger if exists geodata_notify on geodata;
CREATE TRIGGER geodata_notify AFTER INSERT OR UPDATE OR DELETE ON geodata
FOR EACH ROW EXECUTE PROCEDURE notify_trigger(
  'ip',
  'lat',
  'lon',
  'c_code',
  'c_name'
);

