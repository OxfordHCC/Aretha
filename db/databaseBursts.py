import psycopg2, psycopg2.extensions, select, threading, sys, configparser, os

IOTR_BASE = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
CONFIG_PATH = IOTR_BASE + "/config/config.cfg"

class dbManager():
    
    def __init__(self, dbname=None, username=None, password=None):
        
        CONFIG = configparser.ConfigParser()
        CONFIG.read(CONFIG_PATH)

        if dbname is None:
            dbname = CONFIG['postgresql']['database']
        if username is None:
            username = CONFIG['postgresql']['username']
        if password is None:
            password = CONFIG['postgresql']['password']

        try:
            sys.stdout.write("Connecting to database...")
            self.connection = psycopg2.connect("dbname=%(dbname)s user=%(username)s password=%(password)s" % {'dbname':dbname,'username':username,'password':password })
            print("ok connected to database")
        except:
            print("error")

    def listen(self, channel, cb=None):
        try:
            conn = self.connection
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            curs = conn.cursor()
            curs.execute("LISTEN %s ;" % channel)
            stop = [False]
            def stopme(): 
                stop[0] = True
            def subp(): 
                while not stop[0]: # kill me with a sharp stick. 
                    if select.select([conn],[],[],5) == ([],[],[]):
                        # print("Timeout")
                        pass
                    else:
                        conn.poll()
                        while not stop[0] and conn.notifies:
                            notify = conn.notifies.pop(0)
                            # print("Got NOTIFY:", notify.pid, notify.channel, notify.payload)
                            if cb is not None:
                                cb(notify.payload)
            thread = threading.Thread(target=subp)
            thread.start()                
            return stopme
        except:
            print("listen error")
            return lambda: None
        

    def execute(self, query, data, all=True):
        """ 
        Execute the query with data on the postgres db 
        If `all` is False then only gets one entry matching the query
        """
        cur = self.connection.cursor()
        cur.execute(query, data)
        #colnames = [desc[0] for desc in cur.description]
        try:
            if all:
                output = cur.fetchall()
            else:
                output = cur.fetchone()
        except:
            output = ""
        
        self.connection.commit()
        cur.close()

        return output

    def closeConnection(self):
        self.connection.close()

