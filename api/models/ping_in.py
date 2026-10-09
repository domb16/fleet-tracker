from pydantic import BaseModel, Field


class PingIn(BaseModel):
    vehicle_id: int = Field(ge=1, description="Vehicle ID")
    timestamp: int = Field(ge=0, description="Epoch timestamp seconds, UTC")
    lon: float = Field(ge=-180, le=180, allow_inf_nan=False, description="Longitude")
    lat: float = Field(ge=-90, le=90, allow_inf_nan=False,description="Latitude")