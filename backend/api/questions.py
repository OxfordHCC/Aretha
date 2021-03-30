import datetime
import json
from urllib.request import Request, urlopen
from peewee import fn, JOIN


def create_result(text="", impacts=[], geodata=[], devices=[]):
    return {
        "text": text,
        "impacts": impacts,
        "geodata": geodata,
        "devices": devices
    }

def _get_s1():
    return create_result(text="Some content will be illustrated with examples from your home network. When they do, they'll appear here.")

def _get_b4(Transmissions, Geodata, Devices):
    [tx] = (Transmissions
            .select(Transmissions.ext, Transmissions.mac, fn.SUM(Transmissions.bytes))
            .where(Transmissions.proto == 'HTTP')
            .group_by(Transmissions.ext)
            .order_by(fn.SUM(Transmissions.bytes), desc=True)
            .limit(1)
            .dicts())

    [geo] = (Geodata
             .select()
             .where(Geodata.ip == tx['dest'])
             .limit(1)
             .dicts())

    [device] = (Devices
                .select(Devices.name)
                .where(Devices.mac == tx['mac'])
                .dicts())

    company = geo['c_name']
    country = geo['c_code']
    
    return create_result(
        text=f"Did you know that your {device} sends unencrypted data to {company} (in {country})?"
        , impacts=[{
            "company": tx['ext']
            , "device": tx['mac']
            , "impact": tx['bytes']
        }]
        , geodata=[{
            "latitude": geo['lat']
            , "longitude": geo['lon']
            , "ip": tx['ext']
        }]
        , devices=[tx['mac']]
    )

def _get_d2(Transmissions, Devices, Geodata):
    example = (Transmissions
                 .select(Devices.name, fn.COUNT(Geodata.ip.distinct()))
                 .join(Geodata, on=(Transmissions.ext == Geodata.ip))
                 .join(Devices, on=(Transmissions.mac == Devices.mac))
                 .where(Geodata.tracker == True)
                 .group_by(Devices.name)
                 .order_by(fn.COUNT(Geodata.ip.distinct()), desc=True)
                 .tuples())
    
    device = example[0][0]
    single_tracker = example[0][1]
    total_tracker = 0
    
    for record in example:
        total_tracker += record[1]

    return create_result(
        text=f"Across the devices connected to the privacy assistant there are connections to {total_tracker} different companies that have been known to track users across the internet. Did you know that your {device} sends data to {single_tracker} of these companies?"
    )

def _get_d3(Transmissions, Geodata, Devices):
    [example1] = Devices.select(fn.COUNT(Devices.mac).tuples())
    [example2] = (Devices
                  .select(fn.COUNT(Devices.mac.distinct()))
                  .join(Transmissions)
                  .join(Geodata, on=(Transmissions.ext == Geodata.ip))
                  .where(Geodata.c_name == "Google LLC")
                  .tuples())

    return create_result(
        text=f"Of the {example1} devices connected to Aretha, {example2} of them send data to Google.")


def _get_d4(Transmissions, Devices, Geodata):
    example = (Geodata
               .select(Geodata.c_name, Devices.name)
               .join(Transmissions, on=(Geodata.ip == Transmissions.ext))
               .join(Devices, on=(Transmissions.mac == Devices.mac))
               .distinct()
               .tuples())

    req = Request("https://haveibeenpwned.com/api/v2/breaches"
                  , headers={"User-Agent" : "IoT-Refine"})

    with urlopen(req) as url:
        data = json.loads(url.read().decode())
        for company in example:
            device = company[1]
            for breach in data:
                if company[0].strip(" LLC").strip(", Inc.").strip(" Inc.") == breach["Name"]:
                    return create_result(
                    text=f"Did you know that {company[0]} (that communicates with your {device}) was the victim of a data breach on {breach['BreachDate']} where {breach['PwnCount']} records were stolen? If you didn't know about this, you might want to change your passwords with the company.")

    return create_result(text=f"Thankfully, none of your devices communicate with companies on our data breach list.")


def _get_frequency(Transmissions, Devices, Geodata, Exposures):

    [(mac, device, count)] = (Transmissions
                              .select(Devices.mac, Devices.name, fn.SUM(Transmissions.bytes))
                              .join(Devices)
                              .group_by(Devices.mac)
                              .order_by(fn.COUNT(Transmissions.id), desc=True)
                              .limit(1)
                              .tuples())

    [(start_time)] = (Exposures
                      .select(Exposures.start_time)
                      .join(Transmissions, on=(Exposures.id == Transmissions.exposure))
                      .where(Transmissions.mac == mac)
                      .order_by(Exposures.start_time)
                      .limit(1)
                      .tuples())

    [(end_time)] = (Exposures
                    .select(Exposures.end_time)
                    .join(Transmissions, on=(Exposures.id == Transmissions.exposure))
                    .where(Transmissions.mac == mac)
                    .order_by(Exposures.end_time, desc=True)
                    .limit(1)
                    .tuples())

    start = datetime.fromisoformat(str(start_time))
    end = datetime.fromisoformat(str(end_time))

    return create_result(
        text=f"Your {device} has sent {'{:,}'.format(count)} 'packets' of data in the last {(end - start).days} days. On average, that's once every {((end - start) / count).seconds}.{((end - start) / count).microseconds} seconds."
    )

def _get_b3(Transmissions, Devices, Geodata, Exposures):
    [example] = (Exposures
               .select(Devices.name, Devices.c_name, Transmissions.ext)
               .join(Transmissions, JOIN.FULL_OUTER, on=(Transmissions.exposure == Exposures.id))
               .join(Devices, on=(Devices.mac == Transmissions.mac))
               .join(Geodata, on=(Geodata.ip == Transmissions.ext))
               .order_by(Exposures.end_time, desc=True)
               .limit(1)
               .tuples)
    
    return create_result(
        text=f"For example, your {example[0]} just received a packet from {example[1]} which has an IP address of {example[2]}."
    )
            
def get_example(question):
    if question == "S1":
        return _get_s1()
    if question == "S2":
        return _get_s1() # same as S1
    if question == "B4":
        return _get_b4()
    if question == "D2":
        return _get_d2()
    if question == "D3":
        return _get_d3()
    if question == "D4":
        return _get_d4()
    if question == "frequency":
        return _get_frequency()
    if question == "B3":
        return _get_b3()
    return False
        

