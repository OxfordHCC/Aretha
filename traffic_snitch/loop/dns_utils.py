import dns.resolver
import tldextract
from loop import log


def reverse_dns(ip):
    domain = None

    resolver = dns.resolver.Resolver()
    # TODO populate from config file
    resolver.nameservers = ['8.8.8.8', '8.8.4.4']

    try:
        log.debug(f"Attempting reverse DNS resolving {ip}")
        dns_ans = resolver.query(dns.reversename.from_address(ip),'PTR')
        raw_domain = str(dns_ans[0])
        domain = tldextract.extract(raw_domain).registered_domain
        log.debug('Success reverse dns [%s->%s]' % (ip, domain))
    except Exception as e:
        log.error("Error resolving ip %s " % ip, exc_info=e)
    finally:
        return domain


    
    
    
