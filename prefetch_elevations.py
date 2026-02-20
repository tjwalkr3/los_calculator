"""Prefetch elevation data for geographic regions."""

import json
import os
import numpy as np
import requests
from typing import Dict, List, Tuple


class ElevationPrefetcher:
    """Prefetch and cache elevation data for geographic regions."""

    CACHE_FILE = "elevation_cache.json"
    REGIONS = [
        ("Colorado", 37.0, 41.0, -109.0, -102.0),
        ("California", 35.5, 42.0, -124.5, -114.0),
        ("Wyoming", 41.0, 45.0, -111.0, -104.0),
        ("New Mexico", 31.3, 37.0, -109.0, -103.0),
        ("Alaska", 51.0, 71.5, -180.0, -130.0),
        ("Pacific NW", 43.0, 49.0, -125.0, -116.0),
    ]

    def __init__(self, resolution: float = 0.01):
        """
        Initialize prefetcher.

        Args:
            resolution: Grid resolution in degrees (~0.01 = 1km spacing)
        """
        self.resolution = resolution

    def _get_elevations_batch(
        self, coordinates: List[Tuple[float, float]], region_name: str = ""
    ) -> List[float]:
        """Fetch elevations for a batch of coordinates."""
        locations = [{"latitude": lat, "longitude": lon} for lat, lon in coordinates]
        url = "https://api.open-elevation.com/api/v1/lookup"
        chunk_size = 1000
        elevations = []
        total_chunks = (len(locations) + chunk_size - 1) // chunk_size

        for i in range(0, len(locations), chunk_size):
            chunk = locations[i : i + chunk_size]
            chunk_num = i // chunk_size + 1
            progress = (chunk_num / total_chunks) * 100

            if region_name:
                print(
                    f"  Fetching batch {chunk_num}/{total_chunks} ({progress:.1f}%)..."
                )

            try:
                response = requests.post(url, json={"locations": chunk}, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    elevations.extend(result["elevation"] for result in data["results"])
                else:
                    elevations.extend([0.0] * len(chunk))
            except Exception:
                elevations.extend([0.0] * len(chunk))

        return elevations

    def _create_region_grid(
        self, south: float, north: float, west: float, east: float
    ) -> List[Tuple[float, float]]:
        """Create a grid of coordinates covering a geographic region."""
        lats = np.arange(south, north, self.resolution)
        lons = np.arange(west, east, self.resolution)
        lat_grid, lon_grid = np.meshgrid(lats, lons)
        return list(zip(lat_grid.flatten().tolist(), lon_grid.flatten().tolist()))

    def prefetch_elevations(self):
        """Prefetch elevation data for all regions and save to cache file."""
        if os.path.exists(self.CACHE_FILE):
            print(f"Cache file {self.CACHE_FILE} already exists. Skipping prefetch.")
            return

        cache: Dict[str, float] = {}

        print(f"Prefetching elevation data for {len(self.REGIONS)} regions...")
        print(f"Resolution: {self.resolution} degrees (~1km grid spacing)\n")

        for region_idx, (region_name, south, north, west, east) in enumerate(
            self.REGIONS
        ):
            print(f"[{region_idx + 1}/{len(self.REGIONS)}] Processing {region_name}...")
            coords = self._create_region_grid(south, north, west, east)
            print(f"  Grid size: {len(coords):,} points")

            elevations = self._get_elevations_batch(coords, region_name)

            print(f"  Caching {len(coords):,} points...")
            for (lat, lon), elev in zip(coords, elevations):
                key = f"{lat:.6f},{lon:.6f}"
                cache[key] = elev

            print(
                f"  ✓ Completed {region_name} (Total cached: {len(cache):,} points)\n"
            )

        print(f"Saving cache to {self.CACHE_FILE}...")
        with open(self.CACHE_FILE, "w") as f:
            json.dump(cache, f)

        print(f"Done! Cached {len(cache)} elevation points across all regions")
