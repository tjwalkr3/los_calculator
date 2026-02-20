"""Peak data structure definition."""

from typing import TypedDict


class Peak(TypedDict):
    """Type definition for peak dictionary."""
    name: str
    lat: float
    lon: float
    elevation_m: float
