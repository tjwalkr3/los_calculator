"""Main script to analyze line-of-sight for all peak pairs."""

import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from calculate_los import LOSCalculator
from peak_pair_finder import PeakPairFinder
from prefetch_elevations import ElevationPrefetcher
from prefetch_peaks import PeakPrefetcher


def process_peak_pair(peak1, peak2, cache):
    """
    Process a single peak pair for LOS analysis.
    
    Args:
        peak1: First peak dictionary
        peak2: Second peak dictionary
        cache: Elevation cache dictionary
        
    Returns:
        Tuple of (statistics_string, is_clear)
    """
    calculator = LOSCalculator(peak1, peak2, elevation_cache=cache)
    is_clear = calculator.is_line_of_sight_clear()
    
    if is_clear:
        calculator.generate_elevation_profile()
    
    stats = calculator.get_statistics()
    return (stats, is_clear)

print("Step 1: Prefetching peak data...")
peak_prefetcher = PeakPrefetcher(min_elevation_feet=13000)
peak_prefetcher.prefetch_peaks()

print("\nStep 2: Prefetching elevation data...")
elevation_prefetcher = ElevationPrefetcher()
elevation_prefetcher.prefetch_elevations()

print("\nStep 3: Loading elevation cache...")
with open("elevation_cache.json", "r") as f:
    cache = json.load(f)
print(f"Loaded {len(cache)} elevation grid points")

print("\nStep 4: Finding peak pairs...")
finder = PeakPairFinder(min_elevation_feet=13000)
pairs = finder.get_peak_pairs(min_distance_km=350, max_distance_km=600)
print(f"Found {len(pairs)} peak pairs between 400-600km apart")

print("\nStep 5: Analyzing line-of-sight for all pairs...")

# Use more workers than CPU cores to compensate for I/O blocking during plot generation
num_workers = os.cpu_count() or 24
print(f"Using {num_workers} parallel workers to maximize CPU utilization")

statistics_lines = []
clear_count = 0
blocked_count = 0
completed_count = 0

# Process pairs in parallel
with ProcessPoolExecutor(max_workers=num_workers) as executor:
    # Submit all tasks
    future_to_pair = {
        executor.submit(process_peak_pair, peak1, peak2, cache): (peak1, peak2)
        for peak1, peak2 in pairs
    }
    
    # Process results as they complete
    for future in as_completed(future_to_pair):
        completed_count += 1
        
        if completed_count % 100 == 0 or completed_count == len(pairs):
            print(f"  Processed {completed_count}/{len(pairs)} pairs...")
        
        try:
            stats, is_clear = future.result()
            statistics_lines.append(stats)
            statistics_lines.append("")
            
            if is_clear:
                clear_count += 1
            else:
                blocked_count += 1
        except Exception as e:
            print(f"  Error processing pair: {e}")
            blocked_count += 1

print(f"\nStep 6: Saving statistics...")
with open("elevation_profiles/statistics.txt", "w") as f:
    f.write("\n".join(statistics_lines))

print(f"\nComplete!")
print(f"  Total pairs analyzed: {len(pairs)}")
print(f"  Clear LOS: {clear_count}")
print(f"  Blocked LOS: {blocked_count}")
print(f"  Statistics saved to: elevation_profiles/statistics.txt")
print(f"  Elevation profiles saved to: elevation_profiles/")
