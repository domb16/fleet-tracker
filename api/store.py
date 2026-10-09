import sqlite3
import threading

from core_math.core import Point, haversine

MAX_SPEED_MS = 200 / 3.6

def check_ping(last: tuple[int, Point] | None, ts: int, p: Point) -> str | None:

    if last is None:
        return None
    last_ts, last_p = last
    if ts <= last_ts:
        return "out_of_order"
    if haversine(last_p, p) / (ts - last_ts) > MAX_SPEED_MS:
        return "teleport"
    return None


class PingStore:
    def __init__(self, path: str = ":memory:") -> None:
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        self._db.execute("""CREATE TABLE IF NOT EXISTS pings (
                   vehicle_id INTEGER NOT NULL,
                   ts         INTEGER NOT NULL,
                   lon        REAL    NOT NULL,
                   lat        REAL    NOT NULL,
                   PRIMARY KEY (vehicle_id, ts)
               ) WITHOUT ROWID""")
        self._db.commit()


    def add(self, vehicle_id: int, ts: int, p:Point) -> str | None:
        with self._lock:
            row = self._db.execute(
                "SELECT ts, lon, lat FROM pings WHERE vehicle_id = ? ORDER BY ts DESC LIMIT 1",
                (vehicle_id,),
            ).fetchone()
            last = (row[0], Point(row[1], row[2])) if row else None
            reason = check_ping(last, ts, p)
            if reason is None:
                self._db.execute(
                    "INSERT INTO pings (vehicle_id, ts, lon, lat) VALUES (?, ?, ?, ?)",
                    (vehicle_id, ts, p.lon, p.lat),
                )
                self._db.commit()
            return reason


    def track(self, vehicle_id: int) -> list[tuple[int, Point]]:
        with (self._lock):
            rows = self._db.execute(
                "SELECT ts, lon, lat FROM pings WHERE vehicle_id = ? ORDER BY ts", (vehicle_id,),
            ).fetchall()
        return [(ts, Point(lon, lat)) for ts, lon, lat in rows]

def track_to_geojson(vehicle_id: int, points: list[tuple[int, Point]]) -> dict:
    coords = [[p.lon, p.lat] for _, p in points]

    geometry = (
        {"type": "Point", "coordinates": coords[0]}
        if len(coords) == 1
        else {"type": "LineString", "coordinates": coords}
    )

    distance = sum(haversine(a,b) for (_, a), (_, b) in zip(points, points[1:]))
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "vehicle_id": vehicle_id,
            "point_count": len(points),
            "times": [ts for ts, _ in points],
            "distance_m": round(distance, 1)
        },
    }