import psycopg2, psycopg2.extensions, select, threading, sys, configparser, os, datetime, math
import peewee
from playhouse.postgres_ext import PostgresqlExtDatabase
from playhouse.reflection import generate_models, print_model, print_table_sql
from playhouse.shortcuts import model_to_dict
from config import config as CONFIG


class DbManager():
    def __init__(self, dbname=None, username=None, password=None, host=None, port=None):
        if dbname is None:
            dbname = CONFIG['postgresql']['database']
        if username is None:
            username = CONFIG['postgresql']['username']
        if password is None:
            password = CONFIG['postgresql']['password']
        if host is None:
            host = CONFIG['postgresql'].get('host') or 'localhost'
        if port is None:
            port = CONFIG['postgresql'].get('port') or 5432

        try:
            sys.stdout.write("Connecting to database...")

            self.connection = psycopg2.connect(
                dbname=dbname,
                user=username,
                password=password,
                port=port,
                host=host)
            
            self.peewee = PostgresqlExtDatabase(
                dbname,
                user=username,
                password=password,
                host=host,
                port=port)
            
            self._get_models()
            print("ok")
        except:
            print("error")

    def _get_models(self):
        models = generate_models(self.peewee)
        self.Exposures, self.Transmissions = models['exposures'], models['transmissions']

    def listen(self, channel, cb=None):
        try:
            # get connection
            conn = self.connection
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

            # get cursor
            curs = conn.cursor()
            curs.execute("LISTEN %s ;" % channel)

            # stop flag
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
        
        try:
            if all:
                output = cur.fetchall()
            else:
                output = cur.fetchone()
        except:
            output = []
        
        self.connection.commit()
        cur.close()

        return output

    def closeConnection(self):
        self.connection.close()


class Extposure:
    def __init__(self, initial=None):
        self.packets = 0
        self.bytes = 0
        self.bytevar = 0
        self.ext = initial.ext
        self.merge(initial)
        
    def merge(self, transmission):
        assert transmission.ext == self.ext, f"Ext mismatch {self.ext} vs {transmission.ext}"
        self.packets += transmission.packets
        self.bytes += transmission.bytes
        self.bytevar = self._combinevar(self.bytevar, transmission.bytevar)
        return self

    def _combinevar(self, v1, v2):
        return v1 + v2  # TODO

    def to_dict(self):
        return dict( [ (x, self.__getattribute__(x)) for x in ['packets','bytes','bytevar'] ] )
        
class TransMac:
    # mac -> ip exposure
    def __init__(self, tnew):
        self.mac = tnew.mac
        self.by_ext = {}
        self.merge(tnew)

    def merge(self, transmission):
        assert self.mac == transmission.mac, f"internal error: Mac mismatch { self.mac } vs { transmission.mac }"
        self.by_ext[transmission.ext] = self.by_ext.get(transmission.ext) and self.by_ext.get(transmission.ext).merge(transmission) or Extposure(transmission)
        return self

    def to_dict(self):
        return dict([(k,e.to_dict()) for (k,e) in self.by_ext.items()])

class TransEpoch:
    # transepoch has by_mac -> ext
    def __init__(self, transmission=None):
        self.by_mac = {}
        if not transmission is None:
            self.merge(transmission)
        
    def merge(self, transmission):
        tx_mac = self.by_mac.get(transmission.mac)
        if tx_mac is None:
            tx_mac = TransMac(transmission)
        else:
            tx_mac = tx_mac.merge(transmission)

        self.by_mac[transmission.mac] = tx_mac
        
        return self

    def to_dict(self):
        return dict([(mac, trans.to_dict()) for (mac, trans)  in self.by_mac.items()])
    
        
class TransmissionMerger:
    def __init__(self, mins=5):
        self.by_epoch = {}
        self.mins = mins

    def compute_epoch(self, dt):
        # computes the relevant epoch of dt
        return math.floor(dt.timestamp() / (self.mins*60))

    def merge(self, transmission):
        # transmission has to be a peeweemodel joined
        assert transmission.exposure and transmission.exposure.id, "Model must be joined with Exposures"
        epoch = self.compute_epoch(transmission.exposure.start_date)
        if self.by_epoch.get(epoch):
            self.by_epoch[epoch].merge(transmission)
        else:
            self.by_epoch[epoch] = TransEpoch(transmission)

    def iter_by_epoch(self):
        return [x for x in sorted(self.by_epoch.items())]

    def to_dict(self):
        return dict([(epoch, macset.to_dict()) for (epoch, macset) in self.by_epoch.items()])
        
# For a new value newValue, compute the new count, new mean, the new M2.
# mean accumulates the mean of the entire dataset
# M2 aggregates the squared distance from the mean
# count aggregates the number of samples seen so far
def updateVar(count, mean, M2, newValue):
    count += 1
    delta = newValue - mean
    mean += delta / count
    delta2 = newValue - mean
    M2 += delta * delta2
    return (count, mean, M2)

def M2toVar(count, mean, M2):
    if count < 2:
        return float('nan')
    return M2 / count
    
def M2toSampleVar(count, mean, M2):
    if count < 2:
        return float('nan')
    return M2 / (count - 1)

# # Retrieve the mean, variance and sample variance from an aggregate
# def finalize(existingAggregate):
#     (count, mean, M2) = existingAggregate
#     if count < 2:
#         return float('nan')
#     else:
#        (mean, variance, sampleVariance) = (mean, M2 / count, M2 / (count - 1))
#        return (mean, variance, sampleVariance)
