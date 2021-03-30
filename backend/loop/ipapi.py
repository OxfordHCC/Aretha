import logging
from loop.trackers import is_tracker
from loop.dns_utils import reverse_dns

log = logging.getLogger('ip-api')

def get_company_info(ip):
    geodata = {}
    
    if ip is None:
        raise Exception("ip argument missing")

    # http://ip-api.com/json/104.103.245.129?fields=status,message,continentCode,country,countryCode,city,lat,lon,timezone,isp,org,as,reverse

    query_fields=("status", "message", "continentCode", "country",
                  "countryCode", "city", "lat", "lon", "timezone",
                  "isp", "org", "as", "reverse")
    
    log.debug(' Querying IP-API for [%s] ' % ip)

    url = 'http://ip-api.com/json/' + ip + "?fields=%s" % query_fields 
    res = requests.get(url)
    json_data = res.json()

    if data.status_code == 429:
        log.info("We have hit our IP-API.com rate limit - 429 received. Returning and coming back another day")
        return geodata

    if res.status_code == 200:
        log.info(json_data)
        geodata['lat'] = json_data.get('lat')
        geodata['lon'] = json_data.get('lon')
        geodata['tracker'] = is_tracker(ip)
        geodata['orgname'] = json_data.get('org') or json_data.get('as')
        geodata['domain'] = json_data.get('reverse')
        geodata['country'] = json_data.get('countryCode') or json_data.get('continentCode')

    if geodata['domain'] is None:
        geodata['domain'] = reverse_dns(ip)

    return geodata
