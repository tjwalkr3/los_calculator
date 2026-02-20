"""Find and pair peaks in the US."""

import requests
from geopy.distance import geodesic
from typing import List, Tuple

from peak import Peak


class PeakPairFinder:
    """Find peaks over a given elevation and generate valid pairings."""

    def __init__(self, min_elevation_feet: int = 13000):
        """
        Initialize peak finder.

        Args:
            min_elevation_feet: Minimum elevation in feet for peaks to include
        """
        self.min_elevation_feet = min_elevation_feet
        self.min_elevation_m = min_elevation_feet * 0.3048
        self._peaks: List[Peak] = []
        self._peaks_loaded = False

    def _fetch_peaks_from_api(self) -> List[Peak]:
        """Fetch peaks from Overpass API (OpenStreetMap)."""
        min_elev = self.min_elevation_m
        overpass_url = "https://overpass-api.de/api/interpreter"

        regions = [
            (37.0, 41.0, -109.0, -102.0),
            (35.5, 42.0, -124.5, -114.0),
            (41.0, 45.0, -111.0, -104.0),
            (31.3, 37.0, -109.0, -103.0),
            (51.0, 71.5, -180.0, -130.0),
            (43.0, 49.0, -125.0, -116.0),
        ]

        peaks: List[Peak] = []

        for south, north, west, east in regions:
            query = f"""
            [out:json][timeout:60];
            (
              node["natural"="peak"]({south},{west},{north},{east});
            );
            out body;
            """

            try:
                response = requests.post(overpass_url, data={"data": query}, timeout=90)

                if response.status_code != 200:
                    continue

                data = response.json()

                for element in data.get("elements", []):
                    if "tags" in element:
                        tags = element["tags"]
                        if "ele" in tags:
                            try:
                                elevation_m = float(tags["ele"])
                                if elevation_m >= min_elev:
                                    name = tags.get("name", f"Peak_{element['id']}")
                                    peaks.append(
                                        {
                                            "name": name,
                                            "lat": element["lat"],
                                            "lon": element["lon"],
                                            "elevation_m": elevation_m,
                                        }
                                    )
                            except (ValueError, KeyError):
                                continue
            except Exception:
                continue

        return peaks

    def _load_peaks(self):
        """Load peaks from API if not already loaded."""
        if not self._peaks_loaded:
            self._peaks = self._fetch_peaks_from_api()
            self._peaks_loaded = True

    def _calculate_distance_km(self, peak1: Peak, peak2: Peak) -> float:
        """Calculate great-circle distance between two peaks in km."""
        coord1 = (peak1["lat"], peak1["lon"])
        coord2 = (peak2["lat"], peak2["lon"])
        return geodesic(coord1, coord2).km

    def get_peak_pairs(
        self, min_distance_km: float = 300, max_distance_km: float = 600
    ) -> List[Tuple[Peak, Peak]]:
        """
        Get all unique pairs of peaks within specified distance range.

        Args:
            min_distance_km: Minimum distance between peaks in kilometers
            max_distance_km: Maximum distance between peaks in kilometers

        Returns:
            List of tuples, each containing two Peak dictionaries
        """
        self._load_peaks()

        pairs: List[Tuple[Peak, Peak]] = []

        for i in range(len(self._peaks)):
            for j in range(i + 1, len(self._peaks)):
                peak1 = self._peaks[i]
                peak2 = self._peaks[j]

                distance = self._calculate_distance_km(peak1, peak2)

                if min_distance_km <= distance <= max_distance_km:
                    pairs.append((peak1, peak2))

        return pairs
