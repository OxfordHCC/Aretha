from flask import Blueprint

def create_blueprint(Transmissions, Exposures):
    blueprint = Blueprint("impacts", __name__)

    @blueprint.route('/<start>/<end>/<delta>')
    def impacts(start, end, delta):
        try:
            start = datetime.fromtimestamp(int(start))
            end = datetime.fromtimestamp(int(end))

            tr1 = (Transmisisons
                   .select()
                   .limit(1)
                   .order_by(Transmissions.id.desc()))

            if len(tr1):
                interval = math.floor(tr1.end_date - tr1.start_date).total_seconds()                
                if interval > 0 and delta % interval > 0:
                    raise ArethaAPIException(f"Delta must be multiple of resolution {interval} seconds", 422)

                matches = (Transmisisons
                           .select()
                           .join(Exposures)
                           .where(Exposures.start_time >= start, Exposures.end_time <= end))

                tMerger = TransmissionMerger(mins=delta)
                impacts = {}
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
