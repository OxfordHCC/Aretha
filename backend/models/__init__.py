from collections import namedtuple
from peewee import Model
from playhouse.postgres_ext import PostgresqlExtDatabase
from playhouse.reflection import generate_models

db = PostgresqlExtDatabase(None)

# (string, string, string, string, string) -> (db, [Model])
def init_models(database, username, password, host, port):
    
    db.init(database, username, password, host, port)

    # this generates peewee Model objects in a dict keyed by table names
    # e.g.
    # Transmissions = models['transmissions']
    # Transmissions.create()
    models = generate_models(db)
    
    db.close()
    return models
