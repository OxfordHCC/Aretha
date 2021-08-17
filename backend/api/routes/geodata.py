from flask import Blueprint
from models import geodata_util

def create_blueprint(Geodata):
    blueprint = Blueprint("geodata", __name__)

    # get geodata about all known ips
    @blueprint.route('/')
    def geodata():
        geos = (Geodata.select().dicts())

        expanded_geos = [geodata_util.expand_field_name(geo_dict) for geo_dict in geos]
        
        return {
            "geodata": expanded_geos
        }

    return blueprint

