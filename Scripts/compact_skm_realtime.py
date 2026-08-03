#!/usr/bin/env python3
import json
import sys


with open(sys.argv[1], encoding="utf-8") as source:
    feed = json.load(source)

updates = []
for trip in feed.get("trip_updates", []):
    if trip.get("agency_id") != "SKM":
        continue
    for stop in trip.get("stop_times", []):
        departure = stop.get("departure")
        if not departure:
            continue
        updates.append({
            "tripID": trip["trip_id"],
            "stopSequence": stop["stop_sequence"],
            "expectedDeparture": departure,
            "confirmed": stop.get("confirmed", False),
            "platform": stop.get("platform"),
        })

result = {"timestamp": feed["timestamp"], "updates": updates}
with open(sys.argv[2], "w", encoding="utf-8") as output:
    json.dump(result, output, ensure_ascii=False, separators=(",", ":"))
    output.write("\n")

print(f"Wrote {len(updates)} SKM realtime stop updates")
