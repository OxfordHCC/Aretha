--categories table matches readable descriptions to bursts of traffic ("this burst is a weather info request")
drop table if exists categories cascade;
create table categories (
	id SERIAL primary key,
	name varchar(40) not null -- e.g. "Alexa-time" or "Alexa-joke"
);

--collates bursts of traffic and optionally assigns them a category
drop table if exists bursts cascade;
create table bursts (
	id SERIAL primary key,
	category integer references categories --primary key assumed when no column given
);

--store core packet info, and optionally which burst it is part ofi, and which company it represents
drop table if exists packets cascade;
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
create index on packets (time);

drop table if exists devices cascade;
create table devices(
	mac varchar(17) primary key,
	manufacturer varchar(40),
	name varchar(255) DEFAULT 'unknown'
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
drop table if exists models cascade;
create table models (
	id SERIAL primary key,
	device varchar(17) not null, --device mac address
	time timestamp not null, --time the model was made
	destination varchar(20) not null, --name of the company data was sent to
	location varchar(2) not null, --country the company is based in
	impact real not null --amount of traffic in mb
);

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
    'timestamp',CURRENT_TIMESTAMP,
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
CREATE TRIGGER packets_notify AFTER INSERT OR UPDATE OR DELETE ON packets
FOR EACH ROW EXECUTE PROCEDURE notify_trigger(
  'id',
  'mac',
  'src',
  'dst',
  'len',
  'burst'
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
