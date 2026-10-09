import pytest
from fastapi.testclient import TestClient
import pytest
from fastapi.testclient import TestClient

from api.core import create_app
from core_math.core import Point, destination
from mock.fleet_mock_data import generate_rows

LONDON = Point(-0.1278, 51.5074)


@pytest.fixture
def client():
    return TestClient(create_app(":memory:"))


def ping(vid=1, ts=1000, lon=LONDON.lon, lat=LONDON.lat):
    return {"vehicle_id": vid, "timestamp": ts, "lon": lon, "lat": lat}


def test_post_valid_ping(client):
    r = client.post("/pings", json=ping())
    assert r.status_code == 201
    assert r.json() == ping()


@pytest.mark.parametrize("body", [
    ping(lat=91), ping(lat=-91), ping(lon=181), ping(lon=-181),
    ping(vid=0), ping(ts=-1),
    {"vehicle_id": 1, "timestamp": 1000, "lon": 0},   # missing lat
    {"vehicle_id": 1, "timestamp": 1000, "lon": "abc", "lat": 0},
])
def test_post_invalid_shape_is_422(client, body):
    assert client.post("/pings", json=body).status_code == 422


def test_post_nan_is_422(client):
    r = client.post("/pings", content='{"vehicle_id":1,"timestamp":1,"lon":NaN,"lat":0}',
                    headers={"content-type": "application/json"})
    assert r.status_code == 422


def test_post_out_of_order_and_teleport_are_409_with_reason(client):
    client.post("/pings", json=ping(ts=1000))
    r = client.post("/pings", json=ping(ts=999))
    assert (r.status_code, r.json()["detail"]) == (409, {"reason": "out_of_order"})
    r = client.post("/pings", json=ping(ts=1060, lon=-74.006, lat=40.7128))
    assert (r.status_code, r.json()["detail"]) == (409, {"reason": "teleport"})
    assert client.post("/pings", json=ping(ts=1120)).status_code == 201  # good ping after bad


def test_track_unknown_vehicle_404(client):
    assert client.get("/vehicles/5/track").status_code == 404


def test_track_bad_id_422(client):
    assert client.get("/vehicles/0/track").status_code == 422
    assert client.get("/vehicles/abc/track").status_code == 422


def test_track_returns_geojson(client):
    b = destination(LONDON, 0, 500)
    client.post("/pings", json=ping(ts=1000))
    client.post("/pings", json=ping(ts=1060, lon=b.lon, lat=b.lat))
    r = client.get("/vehicles/1/track")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/geo+json")
    body = r.json()
    assert body["geometry"]["type"] == "LineString"
    assert body["geometry"]["coordinates"][0] == [LONDON.lon, LONDON.lat]
    assert body["properties"]["point_count"] == 2


def test_generated_traffic_gets_the_status_the_key_predicts(client):
    expected_status = {"ok": 201, "out_of_order": 409, "teleport": 409, "out_of_range": 422}
    for r in generate_rows(seed=42):
        if r.expected in expected_status:
            resp = client.post("/pings", json={"vehicle_id": r.vehicle_id,
                               "timestamp": r.timestamp, "lon": r.lon, "lat": r.lat})
            assert resp.status_code == expected_status[r.expected], (r, resp.text)


# def test_nearby_