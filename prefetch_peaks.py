"""Prefetch peak data from OpenStreetMap via Overpass API."""

import json
import os
import requests
from typing import List

from peak import Peak


class PeakPrefetcher:
    """Prefetch and cache peak data from OpenStreetMap."""

    CACHE_FILE = "peaks_cache.json"
    REGIONS = [
        ("Colorado", 37.0, 41.0, -109.0, -102.0),
        ("California", 35.5, 42.0, -124.5, -114.0),
        ("Wyoming", 41.0, 45.0, -111.0, -104.0),
        ("New Mexico", 31.3, 37.0, -109.0, -103.0),
        ("Alaska", 51.0, 71.5, -180.0, -130.0),
        ("Pacific NW", 43.0, 49.0, -125.0, -116.0),
    ]

    def __init__(self, min_elevation_feet: int = 13000):
        """
        Initialize peak prefetcher.

        Args:
            min_elevation_feet: Minimum elevation in feet for peaks to include
        """
        self.min_elevation_feet = min_elevation_feet
        self.min_elevation_m = min_elevation_feet * 0.3048

    def _fetch_peaks_for_region(
        self, region_name: str, south: float, north: float, west: float, east: float
    ) -> List[Peak]:
        """Fetch peaks from Overpass API for a specific region."""
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:60];
        (
          node["natural"="peak"]({south},{west},{north},{east});
        );
        out body;
        """

        peaks: List[Peak] = []

        try:
            print(f"  Fetching peaks from Overpass API...")
            response = requests.post(overpass_url, data={"data": query}, timeout=90)

            if response.status_code != 200:
                print(f"  Warning: API request failed with status {response.status_code}")
                return peaks

            data = response.json()

            for element in data.get("elements", []):
                if "tags" in element:
                    tags = element["tags"]
                    if "ele" in tags:
                        try:
                            elevation_m = float(tags["ele"])
                            if elevation_m >= self.min_elevation_m:
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

        except Exception as e:
            print(f"  Error fetching peaks: {e}")

        return peaks

    def prefetch_peaks(self):
        """Prefetch peak data for all regions and save to cache file."""
        if os.path.exists(self.CACHE_FILE):
            print(f"Cache file {self.CACHE_FILE} already exists. Skipping prefetch.")
            return

        all_peaks: List[Peak] = []

        print(f"Prefetching peak data for {len(self.REGIONS)} regions...")
        print(f"Minimum elevation: {self.min_elevation_feet} feet ({self.min_elevation_m:.1f} meters)\n")

        for region_idx, (region_name, south, north, west, east) in enumerate(
            self.REGIONS
        ):
            print(f"[{region_idx + 1}/{len(self.REGIONS)}] Processing {region_name}...")

            peaks = self._fetch_peaks_for_region(region_name, south, north, west, east)

            print(f"  Found {len(peaks)} peaks")
            all_peaks.extend(peaks)
            print(
                f"  ✓ Completed {region_name} (Total peaks: {len(all_peaks)})\n"
            )

        print(f"Saving cache to {self.CACHE_FILE}...")
        with open(self.CACHE_FILE, "w") as f:
            json.dump(all_peaks, f, indent=2)

        print(f"Done! Cached {len(all_peaks)} peaks across all regions")
