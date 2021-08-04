from flask import Blueprint

def create_blueprint(Devices):
    # get the mac address, manufacturer, and custom name of every device
    blueprint = Blueprint("devices", __name__)
    
    @blueprint.route('/')
    def devices():
        devices = dict()
        raw_devices = Devices.select().tuples()

        for mac, manufacturer, name in raw_devices:
            devices[mac] = {
                "manufacturer": manufacturer,
                "name": name
            }

        return {
            "device": devices
        }

    # set the custom name of a device with a given mac
    # TODO this should be a POST request
    @blueprint.route('/set/<mac>/<name>')
    def set_device(mac, name):
        mac_format = re.compile('^(([a-fA-F0-9]){2}:){5}[a-fA-F0-9]{2}$')
        if mac_format.match(mac) is None:
            raise ArethaAPIException("Invalid mac address given")

        Devices.update(name=name).where(Devices.mac == mac)

        return {
            "message": "Device with mac " + mac + " now has name " + name
        }

    return blueprint

