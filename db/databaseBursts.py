"""
Handles all interaction with the database for burstification and categorisation
"""
import psycopg2
import psycopg2.extensions
import select
import threading

class dbManager():
    
    def __init__(self):
        try:
            self.connection = psycopg2.connect("dbname=testdb user=postgres password=password")
        except:
            print("Connection error")
        

    def listen(self, channel, cb=None):
        try:
            conn = self.connection
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            curs = conn.cursor()
            curs.execute("LISTEN %s ;" % channel)
            def subp(): 
                while 1:
                    if select.select([conn],[],[],5) == ([],[],[]):
                        print("Timeout")
                    else:
                        conn.poll()
                        while conn.notifies:
                            notify = conn.notifies.pop(0)
                            print("Got NOTIFY:", notify.pid, notify.channel, notify.payload)
                            if cb is not None:
                                cb(notify.payload)
            thread = threading.Thread(target=subp)
            thread.start()                
        except:
            print("listen error")
        

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

    def getNoBurst(self):
        """ Get rows of packets where burst is NULL """
        query = "SELECT * FROM packets WHERE burst IS NULL ORDER BY id"
        result = self.execute(query, "", all=True)
        return result

    def getNoCat(self):
        """ Get rows of bursts where category is NULL """
        query = "SELECT * FROM bursts WHERE category IS NULL ORDER BY id"
        result = self.execute(query, "", all=True)
        return result

    def getRowsWithBurst(self, burst):
        """ Get rows of packets where burst is the value specified """
        getRows = "SELECT * FROM packets WHERE burst = %s ORDER BY id" % burst
        result = self.execute(getRows, "", all=True)
        return result

    def insertNewBurst(self):
        """ Insert a new burst with no category and return the ID"""
        sql = """INSERT INTO bursts(category) VALUES(NULL) RETURNING id;"""
        resultId = self.execute(sql, "", all=False)[0]
        return resultId

    def updatePacketBurst(self, packet_id, burst_id):
        """ Update packet burst id for the given packet """
        sql = """ UPDATE packets SET burst = %s WHERE id = %s"""
        self.execute(sql, (burst_id, packet_id))

    def addOrGetCategoryNumber(self, category):
        """ Adds a new category with the string category, and returns its id """
        check = """SELECT * FROM categories WHERE name = %s """
        result = self.execute(check, (category, ), all=False)
        if result is not None:
            return result[0]
        else:
            sql = """INSERT INTO categories(name) VALUES(%s) RETURNING id;"""
            resultId = self.execute(sql, (category, ), all=False)[0]
            return resultId

    def updateBurstCategory(self, burst_id, category_id):
        """ Adds the category id to the burst specified by the id """
        sql = """ UPDATE bursts SET category = %s WHERE id = %s"""
        self.execute(sql, (category_id, burst_id))

    def updatePacketBurstBulk(self, packet_ids, burst_ids):
        """ Update packet burst ids for the given packet ids"""
        number = len(packet_ids)
        arraycontents = "%s" + ", %s"*(number-1)

        start = """UPDATE packets SET burst = data_table.burst_id FROM (select unnest(array["""
        middle = """]) as packet_id, unnest(array["""
        end = """]) as burst_id) as data_table WHERE packets.id = data_table.packet_id """

        sql = start + arraycontents + middle + arraycontents + end
        self.execute(sql, packet_ids + burst_ids)

    def closeConnection(self):
        self.connection.close()