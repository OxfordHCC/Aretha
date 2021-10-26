import psycopg2, psycopg2.extensions, select, threading, sys, configparser, os, datetime, math
import peewee
from playhouse.postgres_ext import PostgresqlExtDatabase
from playhouse.reflection import generate_models, print_model, print_table_sql
from playhouse.shortcuts import model_to_dict


class DbManager():
    def __init__(self, database=None, username=None, password=None, host=None, port=5432):
        try:
            sys.stdout.write("Connecting to database...")

            self.connection = psycopg2.connect(
                dbname=database,
                user=username,
                password=password,
                port=port,
                host=host)
            
            print("ok")
        except Exception as e:
            print(e)

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
