"""
Example usage of the LOSCalculator class.
"""

from calculate_los import LOSCalculator
from peak import Peak

peak1: Peak = {
    "name": "Pikes Peak",
    "lat": 38.8409,
    "lon": -105.0423,
    "elevation_m": 4302,
}

peak2: Peak = {
    "name": "Mount Elbert",
    "lat": 39.1178,
    "lon": -106.4454,
    "elevation_m": 4401,
}

calculator = LOSCalculator(peak1, peak2)

if calculator.is_line_of_sight_clear():
    print("Line of sight is CLEAR!\n")
else:
    print("Line of sight is BLOCKED!\n")

print(f"{calculator.get_statistics()}\n")

calculator.generate_elevation_profile()
print("Elevation profile saved to /elevation_profiles")
