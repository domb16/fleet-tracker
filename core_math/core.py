import math
from typing import NamedTuple


EARTH_RADIUS_M = 6371008.8

class Point(NamedTuple):
    lon: float
    lat: float

Box = tuple[float, float, float, float]

def haversine(a: Point, b: Point) -> float:


    phi1 = math.radians(a.lat)
    phi2 = math.radians(b.lat)
    delta_phi = math.radians(b.lat - a.lat)
    delta_lambda = math.radians(b.lon - a.lon)

    h = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    h = min(1.0, max(0.0, h))


    return EARTH_RADIUS_M * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))

def bbox_geo(center: Point, radius_m: float) -> list[Box]:
    ang = radius_m / EARTH_RADIUS_M
    lat = math.radians(center.lat)

    if abs(lat) + ang >= math.pi / 2:
        min_lat = max(-90.0, math.degrees(lat - ang))
        max_lat = min(90.0, math.degrees(lat + ang))
        return [(-180, min_lat, 180, max_lat)]

    min_lat = math.degrees(lat - ang)
    max_lat = math.degrees(lat + ang)

    dlon = math.degrees(math.asin(min(1.0, math.sin(ang) / math.cos(lat))))

    if dlon >= 180:
        return [(-180, min_lat, 180, max_lat)]

    min_lon = center.lon - dlon
    max_lon = center.lon + dlon

    if min_lon < -180:
        return [(min_lon + 360, min_lat, 180, max_lat), (-180, min_lat, max_lon, max_lat)]
    if max_lon > 180:
        return [(min_lon, min_lat, 180.0, max_lat), (-180, min_lat, max_lon - 360, max_lat)]
    return [(min_lon, min_lat, max_lon, max_lat)]

def _on_segment(p: Point, a: Point, b: Point, eps:float=1e-12) -> bool:
    cross = (b.lon - a.lon) * (p.lat - a.lat) - (b.lat - a.lat) * (p.lon - a.lon)

    if abs(cross) > eps:
        return False

    return min(a.lon, b.lon) - eps <= p.lon <= max(a.lon, b.lon) + eps and min(a.lat, b.lat) - eps <= p.lat <= max(a.lat, b.lat) + eps


def point_in_polygon(p: Point, polygon: list[Point]) -> bool:
    n = len(polygon)

    for i in range(n):
        if _on_segment(p, polygon[i-1], polygon[i]):
            return True

    inside = False

    j = n - 1
    for i in range(n):
        a, b = polygon[i], polygon[j]
        if (a.lat > p.lat) != (b.lat > p.lat):
            x_cross = (b.lon - a.lon) * (p.lat - a.lat) / (b.lat - a.lat) + a.lon
            if p.lon < x_cross:
                inside = not inside

        j = i

    return inside

def destination(p: Point, bearing_deg: float, dist_m: float) -> Point:
    d = dist_m / EARTH_RADIUS_M
    brg, lat1, lon1 = map(math.radians, (bearing_deg, p.lat, p.lon))
    lat2 = math.asin(math.sin(lat1) * math.cos(d)
                     + math.cos(lat1) * math.sin(d) * math.cos(brg))
    lon2 = lon1 + math.atan2(math.sin(brg) * math.sin(d) * math.cos(lat1),
                             math.cos(d) - math.sin(lat1) * math.sin(lat2))
    return Point((math.degrees(lon2) + 540) % 360 - 180, math.degrees(lat2))




if __name__ == '__main__':
    lat_london, lon_london = 51.5074, -0.1278
    lat_paris, lon_paris = 48.8566, 2.3522


    distance = haversine(Point(lat_london, lon_london), Point(lat_paris, lon_paris))
    print(f"Distance: {distance:.2f} metres (~{distance / 1000:.2f} km)")
    # Output: Distance: 3435560.85 metres (~343.56 km)