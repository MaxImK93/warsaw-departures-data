#!/usr/bin/env python3
"""Build the compact SKM schedule bundled with the iOS app from Polish rail GTFS."""

import argparse
import csv
import datetime as dt
import io
import json
import zipfile


TARGET_STOPS = {
    "Warszawa Ochota": "warszawa-ochota",
    "Warszawa Śródmieście": "warszawa-srodmiescie",
    "Warszawa Zachodnia": "warszawa-zachodnia",
    "Warszawa Gdańska": "warszawa-gdanska",
}


def rows(archive, filename):
    stream = archive.open(filename)
    text = io.TextIOWrapper(stream, encoding="utf-8-sig", newline="")
    return csv.DictReader(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    parser.add_argument("output")
    args = parser.parse_args()

    with zipfile.ZipFile(args.archive) as archive:
        route_ids = {
            row["route_id"]: row["route_short_name"]
            for row in rows(archive, "routes.txt")
            if row["agency_id"] == "SKM" and row["route_type"] == "2"
        }

        trips = {
            row["trip_id"]: {
                "routeID": route_ids[row["route_id"]],
                "serviceID": row["service_id"],
                "headsign": row["trip_headsign"],
            }
            for row in rows(archive, "trips.txt")
            if row["route_id"] in route_ids
        }

        stop_names = {}
        target_ids = {}
        for row in rows(archive, "stops.txt"):
            stop_names[row["stop_id"]] = row["stop_name"]
            if row["stop_name"] in TARGET_STOPS:
                target_ids[row["stop_id"]] = TARGET_STOPS[row["stop_name"]]

        service_dates = {}
        for row in rows(archive, "calendar_dates.txt"):
            if row["exception_type"] == "1":
                value = row["date"]
                formatted = f"{value[:4]}-{value[4:6]}-{value[6:]}"
                service_dates.setdefault(row["service_id"], []).append(formatted)

        departures = []
        previous = None
        for row in rows(archive, "stop_times.txt"):
            trip = trips.get(row["trip_id"])
            if trip is None:
                previous = None
                continue

            if previous and previous["trip_id"] == row["trip_id"]:
                compact_stop_id = target_ids.get(previous["stop_id"])
                if compact_stop_id:
                    departures.append({
                        "stopID": compact_stop_id,
                        "direction": stop_names.get(row["stop_id"], trip["headsign"]),
                        "routeID": trip["routeID"],
                        "headsign": trip["headsign"],
                        "serviceID": trip["serviceID"],
                        "departureTime": previous["departure_time"],
                        "platform": previous.get("platform") or None,
                        "tripID": previous["trip_id"],
                        "stopSequence": int(previous["stop_sequence"]),
                        "mode": "train",
                    })
            previous = row

        feed_info = next(rows(archive, "feed_info.txt"))
        result = {
            "source": "PKP PLK / SKM Warszawa",
            "sourceURL": "https://mkuran.pl/gtfs/polish_trains.zip",
            "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
            "feedVersion": feed_info.get("feed_version", ""),
            "serviceDates": service_dates,
            "departures": departures,
        }

    with open(args.output, "w", encoding="utf-8") as output:
        json.dump(result, output, ensure_ascii=False, separators=(",", ":"))
        output.write("\n")

    print(f"Wrote {len(departures)} departures to {args.output}")


if __name__ == "__main__":
    main()
