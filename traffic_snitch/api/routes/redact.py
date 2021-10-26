from flask import Blueprint

def create_blueprint(Transmissions, Geodata):
    redact = Blueprint("redact", __name__)

    # TODO see if we can't move these to more generic module (i.e. geodata)
    # return records for the redaction interface
    @redact.route('/')
    def getRedact():
        geodata = list(Geodata.select(Geodata.c_name).distinct().tuples())
        
        return {"geodata": geodata}
    
    # remove records for the redaction interface
    @redact.route('/set/<company>')
    def setRedact(company):
        ips = Geodata.select(Geodata.ip).where(Geodata.c_name == company)
        for ip in ips:
            Transmissions.delete().where(Transmissions.ext == ip[0]).execute()
            Geodata.delete().where(Geodata.ip == ip[0]).execute()

        return {"message": "operation successful"}

    return redact
