# Fleet Tracker

A custom AI-second project to track entities on a global scale using geospatial math, utilising GeoPandas, GeoJSON and FastAPI to make it possible.

### Features:

- Geo math core class ✅
  - _Haversine_ ✅
  - _Geometry boundary box_ ✅
  - _Point in polygon (using ray casting taking antimeridian into account)_ ✅
- Core maths tests ✅
- Ingesting, generating and validating with custom generator simulating rejections with bad data on purpose ✅
- FastAPI barebone structure ✅
  - _POST /pings_ ✅
  - _GET /vehicles/{vehicle_id}/track_ ✅
  - _GET /nearby?lat=&lon=&radius_m=&max_age_s=_ ✅


__TODO__ ⌚

- Finish API test suite 2/3 done
- Geofencing
  - Tracking events: [ENTER/EXIT]
  - Entity states:
    - Pings
    - How long each entity spends within each zone
    - Separate structures currently active and completed visit of each entity for each zone
  - Spatial Indexing
    - Enhance _GET /nearby_ endpoint so it doesn't just do a full scan but separates into either grid indexes or use Shapely's STRtree
    - Benchmark against larger dataset (>100k)
  - Build a front end visualiser
    - React/Typescript/Svelte/Vue (undecided yet)
    - Visualise each live entity position, geofencing and state
    - Update live position via websocket or polling
  - Wrap it all up into a warm and cosy Docker-compose
    - Test and see if API needs ratelimiting.