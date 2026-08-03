#!/usr/bin/env python3
import datetime as dt
import json
import sys


with open(sys.argv[1], encoding="utf-8") as source:
    schedule = json.load(source)

departures = schedule.get("departures", [])
service_dates = [
    dt.date.fromisoformat(value)
    for values in schedule.get("serviceDates", {}).values()
    for value in values
]

if len(departures) < 100:
    raise SystemExit("Schedule contains too few departures")
if not service_dates:
    raise SystemExit("Schedule contains no service dates")
if max(service_dates) < dt.date.today() + dt.timedelta(days=7):
    raise SystemExit("Schedule expires in less than seven days")

print(
    f"Validated {len(departures)} departures, "
    f"valid through {max(service_dates).isoformat()}"
)
