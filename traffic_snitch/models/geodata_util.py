def expand_field_names(geo_dict):
    return {
        "ip": geo_dict['ip'],
        "latitude": geo_dict['lat'],
        "longitude": geo_dict['lon'],
        "country_code": geo_dict['c_code'],
        "company_name": geo_dict['c_name'],
        "domain": geo_dict['domain']
    }
