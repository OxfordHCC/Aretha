from flask import Blueprint
from api.api_exceptions import ArethaAPIException


def create_blueprint(Rules, Content, Devices):

    firewall = Blueprint("firewall", __name__)
    
    # return a list of firewall rules
    @firewall.route('/list')
    def list_rules():
        [(fw_on)] = Content.select(Content.complete).where(Content.name=="S3").tuples()
        rules = list(Rules
                 .select(Rules.id, Rules.device, Devices.name, Rules.c_name)
                 .join(Devices, on=(Rules.device == Devices.mac))
                 .tuples())

        return {
            "rules": rules,
            "enabled": fw_on
        }

    # add a firewall rule as dictated by aretha
    @firewall.route('/enforce/<destination>', methods=["POST"])
    def enforce_dest(destination):
        inserted = Rules.create({
            Rules.c_name: destination
        })

        if not inserted:
            raise ArethaAPIException(f"error while creating destination only rule for {destination}")

        return {"message": f"destination only rule added for {destination}", "success": True}


    # add a firewall rule as dictated by aretha
    @firewall.route('/enforce/<destination>/<device>', methods=["POST"])
    def enforce_dest_dev(destination, device):
        inserted = Rules.create({
            Rules.device: device,
            Rules.c_name: destination
        })

        if not inserted:
            raise ArethaAPIException(f"error while creating device to destination rule for {device} to {destination}")

        return {"message": f"device to destination rule added for {device} to {destination}", "success": True}


    # remove a firewall rule as dictated by aretha
    @firewall.route('/unenforce/<destination>', methods=["POST"])
    def unenforce_dest(destination):
        blocked_ips = DB_MANAGER.execute("""
        SELECT r.c_name, r.device, b.ip 
        FROM rules AS r 
        RIGHT JOIN blocked_ips AS b 
        ON r.id = b.rule 
        WHERE r.c_name = %s AND r.device IS NULL
        """, (destination,))


        # TODO handle other machines
        if sys.platform.startswith("linux"):
            for ip in blocked_ips:
                if ip[1] is None:
                    subprocess.run(["sudo", "iptables", "-D", "INPUT", "-s", ip[2], "-j", "DROP"])
                    subprocess.run(["sudo", "iptables", "-D", "OUTPUT", "-d", ip[2], "-j", "DROP"])
                    subprocess.run(["sudo", "dpkg-reconfigure", "-p", "critical", "iptables-persistent"])

        DB_MANAGER.execute("DELETE FROM rules WHERE c_name = %s AND device IS NULL", (destination,))

        return {"message": f"rule removed for {destination}", "success": True}

    # remove a firewall rule as dictated by aretha
    @firewall.route('/unenforce/<destination>/<device>', methods=["POST"])
    def unenforce_dest_dev(destination, device):
        blocked_ips = DB_MANAGER.execute("""
        SELECT r.c_name, r.device, b.ip 
        FROM rules AS r 
        RIGHT JOIN blocked_ips AS b 
        ON r.id = b.rule 
        WHERE r.c_name = %s and r.device = %s
        """, (destination, device))

        if sys.platform.startswith("linux"):
            for ip in blocked_ips:
                if ip[1] is not None:
                    subprocess.run(["sudo", "iptables", "-D", "FORWARD", "-d", ip[2], "-m", "mac", "--mac-source", ip[1], "-j", "DROP"])
                    subprocess.run(["sudo", "iptables", "-D", "FORWARD", "-s", ip[2], "-m", "mac", "--mac-source", ip[1], "-j", "DROP"])
                    subprocess.run(["sudo", "dpkg-reconfigure", "-p", "critical", "iptables-persistent"])

        DB_MANAGER.execute("DELETE FROM rules WHERE c_name = %s AND device = %s", (destination,device))
        return {"message": f"rule removed for {destination}/{device}", "success": True}


    return firewall

