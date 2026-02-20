"""Main script to analyze line-of-sight for all peak pairs."""

import json
from calculate_los import LOSCalculator
from peak_pair_finder import PeakPairFinder
from prefetch_elevations import ElevationPrefetcher

print("Step 1: Prefetching elevation data...")
prefetcher = ElevationPrefetcher()
prefetcher.prefetch_elevations()

print("\nStep 2: Loading elevation cache...")
with open("elevation_cache.json", "r") as f:
    cache = json.load(f)
print(f"Loaded {len(cache)} elevation grid points")

print("\nStep 3: Finding peak pairs...")
finder = PeakPairFinder(min_elevation_feet=13000)
pairs = finder.get_peak_pairs(min_distance_km=300, max_distance_km=600)
print(f"Found {len(pairs)} peak pairs between 300-600km apart")

print("\nStep 4: Analyzing line-of-sight for all pairs...")

statistics_lines = []
clear_count = 0
blocked_count = 0

for i, (peak1, peak2) in enumerate(pairs):
    if (i + 1) % 100 == 0:
        print(f"  Processed {i + 1}/{len(pairs)} pairs...")

    calculator = LOSCalculator(peak1, peak2, elevation_cache=cache)

    if calculator.is_line_of_sight_clear():
        clear_count += 1
        calculator.generate_elevation_profile()

    stats = calculator.get_statistics()
    statistics_lines.append(stats)
    statistics_lines.append("")

print(f"\nStep 5: Saving statistics...")
with open("elevation_profiles/statistics.txt", "w") as f:
    f.write("\n".join(statistics_lines))

print(f"\nComplete!")
print(f"  Total pairs analyzed: {len(pairs)}")
print(f"  Clear LOS: {clear_count}")
print(f"  Blocked LOS: {blocked_count}")
print(f"  Statistics saved to: elevation_profiles/statistics.txt")
print(f"  Elevation profiles saved to: elevation_profiles/")
