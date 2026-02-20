"""Find and pair peaks in the US."""

import json
import os
from geopy.distance import geodesic
from typing import List, Tuple

from peak import Peak


class PeakPairFinder:
    """Find peaks over a given elevation and generate valid pairings."""

    CACHE_FILE = "peaks_cache.json"

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

    def _load_peaks_from_cache(self) -> List[Peak]:
        """Load peaks from cache file."""
        if not os.path.exists(self.CACHE_FILE):
            raise FileNotFoundError(
                f"{self.CACHE_FILE} not found. Please run peak prefetching first."
            )
        with open(self.CACHE_FILE, "r") as f:
            return json.load(f)

    def _load_peaks(self):
        """Load peaks from cache."""
        if not self._peaks_loaded:
            self._peaks = self._load_peaks_from_cache()
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
