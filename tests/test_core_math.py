import math
import pytest
from core_math.core import Point, EARTH_RADIUS_M, haversine, bbox_geo, point_in_polygon, destination

LONDON = Point(lon=-0.1278, lat=51.5074)
PARIS = Point(lon=2.3522, lat=48.8566)

def in_any(boxes, p: Point, eps=1e-9) -> bool:
    return any(x0 - eps <= p.lon <= x1 + eps and y0 - eps <= p.lat <= y1 + eps
               for x0, y0, x1, y1 in boxes)


def test_london_paris():
    assert haversine(LONDON, PARIS) == pytest.approx(343_556, rel=1e-3)

def test_symmetric():
    assert haversine(LONDON, PARIS) == pytest.approx(haversine(PARIS, LONDON))

def test_same_point_is_zero():
    assert haversine(LONDON, LONDON) == 0

def test_exact_antipode_on_equator():
    assert haversine(Point(0, 0), Point(180, 0)) == pytest.approx(math.pi * EARTH_RADIUS_M)

def test_near_antipodal_does_not_crash():
    d = haversine(Point(10, 20), Point(-170, -20))
    assert d == pytest.approx(math.pi * EARTH_RADIUS_M)

def test_across_antimeridian_is_short():
    assert haversine(Point(179.9, 0), Point(-179.9, 0)) == pytest.approx(22_239, rel=1e-3)

def test_swapped_order_would_be_caught():
    assert haversine(Point(lon=0, lat=0), Point(lon=0, lat=1)) == pytest.approx(111_195, rel=1e-3)


@pytest.mark.parametrize("center, radius", [
    (LONDON, 1_000),
    (Point(25.0, 80.0), 500_000),
    (Point(179.9, 0.0), 50_000),
    (Point(0.0, 0.0), 2_000_000),
])
def test_bbox_contains_whole_circle(center, radius):
    boxes = bbox_geo(center, radius)
    for bearing in range(360):
        assert in_any(boxes, destination(center, bearing, radius)), f"missed bearing {bearing}"

def test_bbox_normal_case_is_one_box():
    assert len(bbox_geo(LONDON, 1_000)) == 1

def test_bbox_antimeridian_splits_in_two():
    boxes = bbox_geo(Point(179.9, 0.0), 50_000)
    assert len(boxes) == 2
    assert in_any(boxes, Point(-179.95, 0.0))

def test_bbox_over_pole_spans_all_longitudes():
    (min_lon, min_lat, max_lon, max_lat), = bbox_geo(Point(0.0, 89.9), 100_000)
    assert (min_lon, max_lon) == (-180, 180)
    assert max_lat == 90


SQUARE = [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)]
L_SHAPE = [Point(0, 0), Point(10, 0), Point(10, 4), Point(4, 4), Point(4, 10), Point(0, 10)]

@pytest.mark.parametrize("p, expected", [
    (Point(5, 5), True), (Point(15, 5), False), (Point(-1, 5), False),
    (Point(5, 0), True), (Point(10, 5), True), (Point(0, 5), True),
    (Point(5, 10), True), (Point(0, 0), True), (Point(10, 10), True),
])
def test_square(p, expected):
    assert point_in_polygon(p, SQUARE) is expected

@pytest.mark.parametrize("p, expected", [
    (Point(2, 8), True), (Point(8, 2), True), (Point(7, 7), False),
    (Point(4, 4), True), (Point(-1, 4), False),
])
def test_l_shape(p, expected):
    assert point_in_polygon(p, L_SHAPE) is expected