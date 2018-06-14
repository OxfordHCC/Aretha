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
        connection = psycopg2.connect("dbname=test")
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
    query = "SELECT * FROM packets WHERE burst == NULL"
    result = execute(query, "", all=True)
    return result

def getNoCat():
    """ Get rows of bursts where category is NULL """
    query = "SELECT * FROM bursts WHERE category == NULL"
    result = execute(query, "", all=True)
    return result

def getRowsWithBurst(burst):
    """ Get rows of packets where burst is the value specified """
    getRows = "SELECT * FROM packets WHERE burst == %s" % burst
    result = execute(getRows, "", all=True)
    return result

def insertNewBurst():
    """ Insert a new burst with no category and return the ID"""
    sql = """INSERT INTO bursts(category) VALUES(%s) RETURNING id;"""
    resultId = execute(sql, "NULL", all=False)[0]
    return resultId

def updatePacketBurst(packet_id, burst_id):
    """ Update packet burst id for the given packet """
    sql = """ UPDATE packets SET burst = %s WHERE id = %s"""
    execute(sql, (burst_id, packet_id))

def addOrGetCategoryNumber(category):
    """ Adds a new category with the string category, and returns its id """
    check = """SELECT * FROM categories WHERE name = %s """
    result = execute(check, category, all=False)
    if result is not None:
        return result[0]
    else:
        sql = """INSERT INTO categories(name) VALUES(%s) RETURNING id;"""
        resultId = execute(sql, category, all=False)[0]
        return resultId

def updateBurstCategory(burst_id, category_id):
    """ Adds the category id to the burst specified by the id """
    sql = """ UPDATE bursts SET category = %s WHERE id = %s"""
    execute(sql, (category_id, burst_id))