import math
from datetime import datetime
from flask import Blueprint
from api.api_exceptions import ArethaAPIException
from models import geodata_util
from models.exposure_util import TransmissionMerger, TransEpoch


# TODO this will be named exposures at some point

def create_blueprint(Transmissions, Exposures, Geodata, Devices):
    blueprint = Blueprint("impacts", __name__)

    # return a dictionary of mac addresses to manufacturers and names
    def get_device_info():
        devices = {}
        raw_devices = Devices.select().dicts()
        for device in iter(raw_devices):
            mac, manufacturer, name = device
            devices[mac] = {"manufacturer": manufacturer, "name": name}
        return devices

    def get_geodata():
        return [geodata_util.expand_field_names(geo_dict)
                for geo_dict in Geodata.select().dicts()]

    @blueprint.route('/<start_timestamp>/<end_timestamp>/<delta>')
    def impacts_range(start_timestamp, end_timestamp, delta):
        try:
            start = datetime.fromtimestamp(int(start_timestamp))
            end = datetime.fromtimestamp(int(end_timestamp))

            impacts = {}

            tr1 = (Transmissions
                   .select()
                   .limit(1)
                   .order_by(Transmissions.id.desc()))


            if (len(tr1)):
                matches = (Transmissisons
                           .select()
                           .join(Exposures)
                           .where(Exposures.start_time >= start, Exposures.end_time <= end))

                tMerger = TransmissionMerger(mins=delta)

                if len(matches) > 0:
                    [tMerger.merge(t) for t in matches]
                    impacts = tMerger.to_dict()

            # add geo and device data
            geos = get_geodata()
            devices = get_device_info()

            return {
                "impacts": impacts,
                "geodata": geos,
                "devices": devices
            }
        except Exception as ae:
            raise ArethaAPIException(internal=ae)

    # return aggregated impacts from <start> to <end>
    # <start>/<end> as unix timestamps
    @blueprint.route('/<start>/<end>')
    def impacts_aggregated(start, end):
        try:
            start, end = datetime.fromtimestamp(int(start)), datetime.fromtimestamp(int(end))
            matches = (Transmissions
                       .select()
                       .join(Exposures)
                       .where(Exposures.start_time >= start, Exposures.end_time <= end))
            result = []

            if len(matches) > 0:
                te = reduce(lambda tres, t: tres.merge(t), matches[1:], TransEpoch(matches[0]))
                for (mac, tm) in te.by_mac.items():
                    for (ext, extp) in tm.by_ext.items():
                        d = extp.to_dict()
                        d.update({"company": ext, "impact": extp.bytes, "device": mac})
                        result.append(d)

            # add geo and device data
            geos = get_geodata()
            devices = get_device_info()

            return {
                "impacts": result,
                "geodata": geos,
                "devices": devices
            }
        except Exception as ae:
            raise ArethaAPIException(internal=ae)


    return blueprint
