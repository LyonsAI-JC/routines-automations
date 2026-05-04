"""Fetch Open-Meteo weather for the upcoming weekend across configured
locations and write the raw forecast data to weather.json.

Designed to run from GitHub Actions. The Claude routine consumes the
committed JSON to do the riding assessment, calendar check, and email.
"""

import json
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

TIMEZONE = "Australia/Melbourne"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OUTPUT_PATH = "weekend-ride-checker/weather.json"

LOCATIONS = [
    # Origin / reference
    {"name": "Springvale",         "lat": -37.9500, "lng": 145.1500},
    {"name": "Melbourne",          "lat": -37.8136, "lng": 144.9631},
    # Dandenong Ranges
    {"name": "Gembrook",           "lat": -37.9483, "lng": 145.5694},
    # Yarra Ranges / Yarra Valley
    {"name": "Healesville",        "lat": -37.6536, "lng": 145.5167},
    {"name": "Warburton",          "lat": -37.7556, "lng": 145.6856},
    {"name": "Mount Donna Buang",  "lat": -37.7000, "lng": 145.7000},
    # Reefton Spur (midpoint of the road between Marysville and Warburton)
    {"name": "Reefton Spur",       "lat": -37.6500, "lng": 145.8000},
    # Alpine
    {"name": "Marysville",         "lat": -37.5160, "lng": 145.7440},
    {"name": "Lake Mountain",      "lat": -37.5167, "lng": 145.8833},
    # High Country
    {"name": "Jamieson",           "lat": -37.2980, "lng": 146.1330},
]

DAILY_FIELDS = [
    "weathercode",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "windspeed_10m_max",
    "windgusts_10m_max",
    "winddirection_10m_dominant",
    "relative_humidity_2m_mean",
    "et0_fao_evapotranspiration",
    "uv_index_max",
    "sunrise",
    "sunset",
]


def upcoming_weekend(today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    days_until_sat = (5 - today.weekday()) % 7
    sat = today + timedelta(days=days_until_sat)
    return sat, sat + timedelta(days=1)


def fetch_forecast(lat: float, lng: float, start: date, end: date) -> dict:
    params = {
        "latitude": lat,
        "longitude": lng,
        "daily": ",".join(DAILY_FIELDS),
        "timezone": TIMEZONE,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    url = f"{OPEN_METEO_URL}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read())


def main() -> int:
    sat, sun = upcoming_weekend()
    # Wed/Thu/Fri before the weekend - used by the routine to assess whether
    # roads will be wet or dry come Saturday.
    prior_days = [sat - timedelta(days=n) for n in (3, 2, 1)]
    start, end = prior_days[0], sun
    print(f"Fetching weather {start} to {end}", file=sys.stderr)

    locations_data = []
    for loc in LOCATIONS:
        raw = fetch_forecast(loc["lat"], loc["lng"], start, end)
        locations_data.append({
            "name": loc["name"],
            "latitude": loc["lat"],
            "longitude": loc["lng"],
            "daily": raw["daily"],
            "daily_units": raw["daily_units"],
        })

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "timezone": TIMEZONE,
        "weekend": {"saturday": sat.isoformat(), "sunday": sun.isoformat()},
        "prior_days": [d.isoformat() for d in prior_days],
        "source": "https://open-meteo.com",
        "locations": locations_data,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {OUTPUT_PATH} ({len(locations_data)} locations)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
