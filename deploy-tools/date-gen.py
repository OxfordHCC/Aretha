#! /usr/bin/env python3

import datetime
import sys

start = datetime.datetime.strptime(sys.argv[1].rstrip(), "%Y-%m-%d")

print("Starting on ", start)
print("Ending on ", start + datetime.timedelta(weeks=6))
print("Paste the following into db/schema.sql when deploying the assistant")
print("")

print("--phase 1")
print("('S1', '" + start.isoformat() + "'),")
print("('S2', '" + start.isoformat() + "'),")

print("--phase 2")
print("('B1', '" + (start + datetime.timedelta(weeks=2)).isoformat() +  "'),")
print("('B2', '" + (start + datetime.timedelta(weeks=2, days=2)).isoformat() +  "'),")
print("('B3', '" + (start + datetime.timedelta(weeks=2, days=4)).isoformat() +  "'),")
print("('B4', '" + (start + datetime.timedelta(weeks=2, days=6)).isoformat() +  "'),")
print("('D1', '" + (start + datetime.timedelta(weeks=2, days=6)).isoformat() +  "'),")
print("('D2', '" + (start + datetime.timedelta(weeks=2, days=8)).isoformat() +  "'),")
print("('D3', '" + (start + datetime.timedelta(weeks=2, days=10)).isoformat() +  "'),")
print("('D4', '" + (start + datetime.timedelta(weeks=2, days=12)).isoformat() +  "'),")

print("--phase 3")
print("('S3', '" + (start + datetime.timedelta(weeks=2, days=14)).isoformat() +  "'),")
print("('SD1', '" + (start + datetime.timedelta(weeks=2, days=16)).isoformat() +  "');")
