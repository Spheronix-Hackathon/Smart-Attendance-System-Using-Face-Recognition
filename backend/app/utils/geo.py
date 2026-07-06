from __future__ import annotations

import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def is_within_radius(lat: float | None, lon: float | None, campus_lat: float, campus_lon: float, max_distance_km: float) -> tuple[bool, float | None]:
    if lat is None or lon is None:
        return False, None
    distance = haversine_km(lat, lon, campus_lat, campus_lon)
    return distance <= max_distance_km, distance
