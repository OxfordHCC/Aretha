import dns
import tldextract
import logging

log = logging.getLogger('dns_utils')
log.setLevel(logging.DEBUG)

def reverse_dns(ip):
    domain = None

    resolver = dns.resolver.Resolver()
    # TODO populate from config file
    resolver.nameservers = ['8.8.8.8', '8.8.4.4']

    try:
        log.info('Attempting reverse DNS resolving [%s]' % ip)
        dns_ans = dns.resolver.query(dns.reversename.from_address(ip),'PTR')
        raw_domain = str(dns_ans[0])
        domain = tldextract.extract(raw_domain).registered_domain
        log.info('Success rdns [%s->%s]' % (ip, domain))
    except Exception as e:
        log.error("Error resolving ip %s " % ip, exc_info=e)
    finally:
        return domain


    
    
    
