#!/usr/bin/env python3
"""
Generate 1-degree grid coordinates for Indonesia
Creates a higher resolution grid than the current 3-degree spacing
"""

import json

def generate_1degree_grid():
    """Generate 1-degree grid covering Indonesia"""
    
    # Indonesia bounding box: -11 to 6 latitude, 95 to 141 longitude
    lat_min, lat_max = -11, 6
    lon_min, lon_max = 95, 141
    
    # Generate coordinates with 1-degree spacing
    latitudes = []
    longitudes = []
    
    for lat in range(lat_min, lat_max + 1):
        for lon in range(lon_min, lon_max + 1):
            latitudes.append(f"{lat:.4f}")
            longitudes.append(f"{lon:.4f}")
    
    grid_data = {
        "latitude": ",".join(latitudes),
        "longitude": ",".join(longitudes),
        "grid_size": 1,
        "total_points": len(latitudes),
        "description": "1-degree grid covering Indonesia (-11 to 6 lat, 95 to 141 lon)"
    }
    
    return grid_data

def main():
    """Generate and save 1-degree grid data"""
    print("Generating 1-degree grid for Indonesia...")
    
    grid_data = generate_1degree_grid()
    
    # Save to file
    output_file = "gridData_1degree.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(grid_data, f, indent=2)
    
    print(f"Generated {grid_data['total_points']} grid points")
    print(f"Grid size: {grid_data['grid_size']} degree")
    print(f"Saved to: {output_file}")
    
    # Also save to parent directory for compatibility
    parent_file = "../gridData_1degree.json"
    with open(parent_file, 'w', encoding='utf-8') as f:
        json.dump(grid_data, f, indent=2)
    
    print(f"Also saved to: {parent_file}")

if __name__ == "__main__":
    main() 