"""
Line-of-sight calculator class for analyzing visibility between two peaks.

This module accounts for Earth's curvature with standard atmospheric refraction (k=4/3).
It uses the open-elevation API to retrieve terrain elevation data.

Example usage:
    peak1 = {
        "name": "Pikes Peak",
        "lat": 38.8409,
        "lon": -105.0423,
        "elevation_m": 4302,
    }
    peak2 = {
        "name": "Mount Elbert",
        "lat": 39.1178,
        "lon": -106.4454,
        "elevation_m": 4401,
    }

    calculator = LOSCalculator(peak1, peak2)

    if calculator.is_line_of_sight_clear():
        print("Clear line of sight!")

    print(calculator.get_statistics())
    calculator.generate_elevation_profile()
"""

import numpy as np
import numpy.typing as npt
import matplotlib.pyplot as plt
import requests
from geopy.distance import geodesic

from peak import Peak


class LOSCalculator:
    """Calculate line-of-sight between two peaks accounting for Earth's curvature."""

    R_EARTH_KM = 6371.0
    REFRACTION_FACTOR = 4.0 / 3.0
    NUM_SAMPLES = 200

    def __init__(self, peak1: Peak, peak2: Peak):
        """
        Initialize calculator with two peaks.

        Args:
            peak1: Dict with keys: name, lat, lon, elevation_m
            peak2: Dict with keys: name, lat, lon, elevation_m
        """
        self.peak1 = peak1
        self.peak2 = peak2
        self._calculated = False
        self._distance_km: float = 0.0
        self._los_limit_km: float = 0.0
        self._terrain_array: npt.NDArray[np.float64] = np.array([])
        self._distances: npt.NDArray[np.float64] = np.array([])
        self._los_line: npt.NDArray[np.float64] = np.array([])
        self._curvature_drop_m: float = 0.0
        self._is_clear: bool = False

    def _calculate(self):
        """Perform all calculations (called lazily)."""
        if self._calculated:
            return

        coord1 = (self.peak1["lat"], self.peak1["lon"])
        coord2 = (self.peak2["lat"], self.peak2["lon"])
        self._distance_km = geodesic(coord1, coord2).km

        self._los_limit_km = 3.57 * (
            np.sqrt(self.peak1["elevation_m"]) + np.sqrt(self.peak2["elevation_m"])
        )

        lats = np.linspace(self.peak1["lat"], self.peak2["lat"], self.NUM_SAMPLES)
        lons = np.linspace(self.peak1["lon"], self.peak2["lon"], self.NUM_SAMPLES)

        terrain_elevations = self._get_elevations(lats, lons)
        self._terrain_array = np.array(terrain_elevations)

        self._terrain_array[0] = self.peak1["elevation_m"]
        self._terrain_array[-1] = self.peak2["elevation_m"]

        self._distances, self._los_line = self._compute_los_line()

        R_effective = self.REFRACTION_FACTOR * self.R_EARTH_KM
        midpoint_distance_km = self._distance_km / 2
        self._curvature_drop_m = (midpoint_distance_km * 1000) ** 2 / (
            2 * R_effective * 1000
        )

        self._is_clear = bool(np.all(self._terrain_array <= self._los_line))

        self._calculated = True

    def _get_elevations(self, latitudes, longitudes):
        """Query Open-Elevation API in chunks."""
        locations = [
            {"latitude": lat, "longitude": lon}
            for lat, lon in zip(latitudes, longitudes)
        ]
        url = "https://api.open-elevation.com/api/v1/lookup"
        chunk_size = 100
        elevations = []

        for i in range(0, len(locations), chunk_size):
            chunk = locations[i : i + chunk_size]
            response = requests.post(url, json={"locations": chunk}, timeout=20)
            if response.status_code == 200:
                data = response.json()
                elevations.extend(result["elevation"] for result in data["results"])
            else:
                raise RuntimeError(
                    f"Elevation API request failed with status code {response.status_code}"
                )

        return elevations

    def _compute_los_line(self):
        """Compute LOS line accounting for Earth's curvature with atmospheric refraction."""
        R_effective = self.REFRACTION_FACTOR * self.R_EARTH_KM

        distances = np.linspace(0, self._distance_km, self.NUM_SAMPLES)

        straight_line = self.peak1["elevation_m"] + (
            self.peak2["elevation_m"] - self.peak1["elevation_m"]
        ) * (distances / self._distance_km)

        earth_bulge_m = (
            -(distances * 1000)
            * ((self._distance_km - distances) * 1000)
            / (2 * R_effective * 1000)
        )

        los_line = straight_line + earth_bulge_m

        return distances, los_line

    def is_line_of_sight_clear(self):
        """
        Check if line-of-sight is clear between the two peaks.

        Returns:
            bool: True if LOS is clear, False if blocked by terrain
        """
        if not self._calculated:
            self._calculate()
        return self._is_clear

    def get_statistics(self):
        """
        Get formatted statistics string.

        Returns:
            str: Formatted statistics including distance, LOS limit, curvature, and clearance
        """
        if not self._calculated:
            self._calculate()

        stats = []
        stats.append(
            f"Peak 1: {self.peak1['name']} ({self.peak1['lat']}, {self.peak1['lon']})"
        )
        stats.append(
            f"Peak 2: {self.peak2['name']} ({self.peak2['lat']}, {self.peak2['lon']})"
        )
        stats.append(f"Great-circle distance: {self._distance_km:.2f} km")
        stats.append(f"Theoretical LOS limit: {self._los_limit_km:.2f} km")
        stats.append(
            f"Earth curvature drop at midpoint: {self._curvature_drop_m:.1f} m (with refraction)"
        )
        stats.append(
            f"Line-of-sight is {'CLEAR' if self._is_clear else 'BLOCKED'} by terrain."
        )

        return "\n".join(stats)

    def generate_elevation_profile(self):
        """
        Generate and save elevation profile graph.

        The file is saved as {peak1_name}_to_{peak2_name}.png (lowercase, no spaces).
        """
        if not self._calculated:
            self._calculate()

        plt.style.use("seaborn-v0_8")
        plt.figure(figsize=(12, 6))

        plt.plot(
            self._distances,
            self._terrain_array,
            label="Terrain Elevation",
            color="sienna",
            linewidth=2,
        )

        plt.plot(
            self._distances,
            self._los_line,
            label="Line of Sight (with Earth curvature)",
            color="royalblue",
            linestyle="--",
            linewidth=2,
        )

        straight_line = self.peak1["elevation_m"] + (
            self.peak2["elevation_m"] - self.peak1["elevation_m"]
        ) * (self._distances / self._distances[-1])
        plt.plot(
            self._distances,
            straight_line,
            label="Straight line (no curvature)",
            color="black",
            linestyle=":",
            linewidth=1.5,
            alpha=0.7,
        )

        plt.xlabel("Distance along path (km)", fontsize=11)
        plt.ylabel("Elevation (m)", fontsize=11)
        plt.title(
            f"Elevation Profile: {self.peak1['name']} to {self.peak2['name']}",
            fontsize=13,
        )
        plt.legend(loc="best")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        name1 = self.peak1["name"].lower().replace(" ", "_")
        name2 = self.peak2["name"].lower().replace(" ", "_")
        distance_km = int(round(self._distance_km))
        filename = f"elevation_profiles/{name1}_to_{name2}_{distance_km}km.png"

        plt.savefig(filename)
        plt.close()
