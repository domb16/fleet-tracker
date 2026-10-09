import os

from fastapi import FastAPI, HTTPException, status
from fastapi.params import Query
from typing import Annotated
from fastapi.responses import JSONResponse

from api.store import PingStore
from api.models.ping_in import PingIn
from api.store import track_to_geojson
from core_math.core import Point


def create_app(db_path: str | None = None) -> FastAPI:
    store = PingStore(db_path or os.environ.get("PING_DB_PATH", "pings.db"))


    app = FastAPI(title="Fleet Tracker", version="1.0.0")

    @app.post("/pings", status_code=status.HTTP_201_CREATED)
    async def post_ping(ping: PingIn):
        reason = store.add(ping.vehicle_id, ping.timestamp, Point(ping.lat, ping.lon))
        if reason is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"reason": reason})
        return ping

    @app.get("/vehicles/{vehicle_id}/track")
    async def get_vehicle_track(vehicle_id: int):
        points = store.track(vehicle_id)

        if not points:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"reason": "No pings for this vehicle."})
        return JSONResponse(track_to_geojson(vehicle_id, points), media_type="application/geo+json")

    @app.get("/nearby")
    async def get_nearby(
            lat: Annotated[float, Query(ge=-90, le=90)],
            lon: Annotated[float, Query(ge=-180, le=180)],
            radius_m: Annotated[float, Query(gt=0, le=50_000) ]= 1_000,
            limit: Annotated[int, Query(ge=1, le=500)] = 100,
            max_age_s: Annotated[int, Query(ge=0, le=1_000_000)] = 100_000):

        return {
            "target_lat": lat,
            "target_lon": lon,
            "radius": radius_m,
            "limit": limit,
            "max_age_s": max_age_s,
        }

    return app