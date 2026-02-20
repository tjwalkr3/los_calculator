"""
Example usage of the PeakFinder class.
"""

from peak_pair_finder import PeakPairFinder

finder = PeakPairFinder(min_elevation_feet=13000)

pairs = finder.get_peak_pairs(min_distance_km=300, max_distance_km=600)

print(f"Found {len(pairs)} peak pairs between 300-600km apart")
print(f"\nFirst 5 pairs:")
for i, (peak1, peak2) in enumerate(pairs[:5]):
    print(f"{i+1}. {peak1['name']} to {peak2['name']}")
