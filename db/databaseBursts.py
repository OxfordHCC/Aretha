"""
Handles all interaction with the database for burstification and categorisation
"""
import psycopg2

def execute(query, data, all=True):
    """ 
    Execute the query with data on the postgres db 
    If `all` is False then only gets one entry matching the query
    """
    try:
        connection = psycopg2.connect("dbname=static user=postgres password=password")
    except:
        print("Connection error")
    else:
        cur = connection.cursor()
        cur.execute(query, data)
        #colnames = [desc[0] for desc in cur.description]
        try:
            if all:
                output = cur.fetchall()
            else:
                output = cur.fetchone()
        except:
            output = ""
        
        connection.commit()
        cur.close()
        connection.close()

        return output

def getNoBurst():
    """ Get rows of packets where burst is NULL """
    query = "SELECT * FROM packets WHERE burst IS NULL ORDER BY id"
    result = execute(query, "", all=True)
    return result

def getNoCat():
    """ Get rows of bursts where category is NULL """
    query = "SELECT * FROM bursts WHERE category IS NULL ORDER BY id"
    result = execute(query, "", all=True)
    return result

def getRowsWithBurst(burst):
    """ Get rows of packets where burst is the value specified """
    getRows = "SELECT * FROM packets WHERE burst = %s ORDER BY id" % burst
    result = execute(getRows, "", all=True)
    return result

def insertNewBurst():
    """ Insert a new burst with no category and return the ID"""
    sql = """INSERT INTO bursts(category) VALUES(NULL) RETURNING id;"""
    resultId = execute(sql, "", all=False)[0]
    return resultId

def updatePacketBurst(packet_id, burst_id):
    """ Update packet burst id for the given packet """
    sql = """ UPDATE packets SET burst = %s WHERE id = %s"""
    execute(sql, (burst_id, packet_id))

def addOrGetCategoryNumber(category):
    """ Adds a new category with the string category, and returns its id """
    check = """SELECT * FROM categories WHERE name = %s """
    result = execute(check, (category, ), all=False)
    if result is not None:
        return result[0]
    else:
        sql = """INSERT INTO categories(name) VALUES(%s) RETURNING id;"""
        resultId = execute(sql, (category, ), all=False)[0]
        return resultId

def updateBurstCategory(burst_id, category_id):
    """ Adds the category id to the burst specified by the id """
    sql = """ UPDATE bursts SET category = %s WHERE id = %s"""
    execute(sql, (category_id, burst_id))

def updatePacketBurstBulk(packet_ids, burst_ids):
    """ Update packet burst ids for the given packet ids"""
    number = len(packet_ids)
    arraycontents = "%s" + ", %s"*(number-1)

    start = """UPDATE packets SET burst = data_table.burst_id FROM (select unnest(array["""
    middle = """]) as packet_id, unnest(array["""
    end = """]) as burst_id) as data_table WHERE packets.id = data_table.packet_id """

    sql = start + arraycontents + middle + arraycontents + end
    execute(sql, packet_ids + burst_ids)