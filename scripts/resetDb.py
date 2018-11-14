#import psycopg2, os, time, datetime, sys, socket, json
import os
import databaseBursts
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
DB_MANAGER = databaseBursts.dbManager()
DB_MANAGER.execute(open(os.path.join(os.path.dirname(FILE_PATH), "db", "schema.sql"), "rb").read(), "")
