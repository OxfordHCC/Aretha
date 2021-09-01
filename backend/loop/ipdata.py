import logging
from loop.trackers import is_tracker
from loop.dns_utils import reverse_dns
from util.config import config

log = logging.getLogger('ipdata')
log.setLevel(logging.DEBUG)

def get_company_info(ip):
    geodata = {}
    
    if ip is None:
        raise Exception("ip argument missing")

    api_key = config['geoapi'].get('key')
    if api_key is None:
        raise Exception("Key is required for ipdata.co and not found in config.cfg")
    
    log.debug('Querying IPData for [%s] ' % ip)

    url = 'https://api.ipdata.co/' + ip + '?api-key=' + api_key
    res = requests.get(url)
    json_data = res.json()

    if res.status_code==200 and json_data['latitude'] is not None:
        log.info(json_data)
        geodata['lat'] = json_data.get('latitude')
        geodata['lon'] = json_data.get('longitude')
        geodata['country'] = json_data.get('country_code') or json_data.get('continent_code')
        geodata['tracker'] = is_tracker(ip)
        geodata['orgname'] = json_data.get('asn',{}).get('name')
        geodata['domain'] = json_data.get('asn',{}).get('domain')
        
    if geodata['domain'] is None:
        geodata['domain'] = reverse_dns(ip)

    return geodata
