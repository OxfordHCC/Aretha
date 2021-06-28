from flask import Blueprint

def create_blueprint(Geodata):
    blueprint = Blueprint("geodata", __name__)

    # get geodata about all known ips
    @blueprint.route('/')
    def geodata():
        geos = (Geodata
                .select(
                    Geodata.ip,
                    Geodata.lat,
                    Geodata.lon,
                    Geodata.c_code,
                    Geodata.c_name,
                    Geodata.domain)
                .dicts())

        return {
            "geodata": geos
        }

    return blueprint

