import csv
import math
import random
from dataclasses import dataclass
from core_math.core import Point, destination
import geopandas as gpd
import pandas as pd
MAX_SPEED_MS = 200 / 3.6
SCENARIOS = (
    "out_of_order", "duplicate_ts", "teleport", "fast_bad", "fast_ok",
    "out_of_range", "not_a_number", "bad_timestamp", "non_numeric_lat", "missing_field",
)

@dataclass
class Row:
    vehicle_id: int
    timestamp: int | str
    lon: float | str
    lat: float | str
    expected: str = "ok"


def generate_rows(seed: int, n_vehicles: int = 3, steps: int = 30,
                  base_epoch: int = 1_790_000_000,
                  origin: Point = Point(-0.1278, 51.5074)) -> list[Row]:
    if steps < len(SCENARIOS) + 2:
        raise ValueError(f"steps must be at least {len(SCENARIOS) + 2}")
    rng = random.Random(seed)
    queues = [_vehicle_rows(rng, v, steps, base_epoch, origin)
              for v in range(1, n_vehicles + 1)]
    return _interleave(rng, queues)


def _pt(p: Point) -> Point:
    return Point(round(p.lon, 6), round(p.lat, 6))


def _vehicle_rows(rng, vid, steps, base_epoch, origin) -> list[Row]:
    last_pt = _pt(Point(origin.lon + rng.uniform(-0.05, 0.05),
                        origin.lat + rng.uniform(-0.05, 0.05)))
    last_ts = base_epoch + rng.randint(0, 30)
    ts = last_ts
    heading = rng.uniform(0, 360)

    scenario_at = dict(zip(rng.sample(range(1, steps), len(SCENARIOS)),
                           rng.sample(SCENARIOS, len(SCENARIOS))))

    rows = [Row(vid, last_ts, last_pt.lon, last_pt.lat)]
    for step in range(1, steps):
        ts += rng.randint(45, 90)
        dt = ts - last_ts
        kind = scenario_at.get(step)

        if kind == "fast_ok":
            speed = 54
        else:
            if kind:
                rows.append(_bad_row(rng, kind, vid, ts, last_ts, last_pt))
            heading = (heading + rng.gauss(0, 15)) % 360
            speed = rng.uniform(5, 30)

        last_pt = _pt(destination(last_pt, heading, speed * dt))
        last_ts = ts
        rows.append(Row(vid, ts, last_pt.lon, last_pt.lat))
    return rows


def _bad_row(rng, kind, vid, ts, last_ts, last_pt) -> Row:
    lon, lat = last_pt
    bearing = rng.uniform(0, 360)
    if kind == "out_of_order":
        return Row(vid, last_ts - rng.randint(1, 3600), lon, lat, "out_of_order")
    if kind == "duplicate_ts":
        p = _pt(destination(last_pt, bearing, 10))
        return Row(vid, last_ts, p.lon, p.lat, "out_of_order")
    if kind == "teleport":
        p = _pt(destination(last_pt, bearing, rng.uniform(50_000, 5_000_000)))
        return Row(vid, ts, p.lon, p.lat, "teleport")
    if kind == "fast_bad":  # just over the speed limit, must be rejected
        p = _pt(destination(last_pt, bearing, 58 * (ts - last_ts)))
        return Row(vid, ts, p.lon, p.lat, "teleport")
    if kind == "out_of_range":
        sign = rng.choice([-1, 1])
        if rng.random() < 0.5:
            return Row(vid, ts, lon, sign * rng.uniform(90.5, 500), "out_of_range")
        return Row(vid, ts, sign * rng.uniform(180.5, 999), lat, "out_of_range")
    if kind == "not_a_number":
        return Row(vid, ts, math.nan, math.nan, "not_a_number")
    if kind == "bad_timestamp":
        return Row(vid, "yesterday", lon, lat, "malformed")
    if kind == "non_numeric_lat":
        return Row(vid, ts, lon, "abc", "malformed")
    if kind == "missing_field":
        return Row(vid, ts, "", lat, "malformed")
    raise ValueError(f"unknown scenario: {kind}")



def _interleave(rng, queues) -> list[Row]:
    queues = [list(reversed(q)) for q in queues]
    out = []
    while any(queues):
        out.append(rng.choice([q for q in queues if q]).pop())
    return out


def write_csv(rows: list[Row], path: str) -> dict[int, str]:
    # probabyl fine for this but better to pickle and unpickle instead of csv
    key = {}
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["vehicle_id", "timestamp", "lon", "lat"])
        for n, r in enumerate(rows, start=1):
            w.writerow([r.vehicle_id, r.timestamp, r.lon, r.lat])
            if r.expected != "ok":
                key[n] = r.expected
    return key


def to_gdf(rows: list[Row]):
    df = pd.DataFrame(rows)
    for col in ("timestamp", "lon", "lat"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")