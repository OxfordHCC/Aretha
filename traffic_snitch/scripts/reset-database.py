#! /usr/bin/env python3

import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
DB_MANAGER = databaseBursts.dbManager()
schema = open(os.path.join(os.path.dirname(FILE_PATH), "db", "schema.sql"), "rb").read()
DB_MANAGER.execute(schema, None)
print("Database sucessfully reset")
