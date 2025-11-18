#!/usr/bin/env python3
"""
OpenMeteo Grid Weather Data Fetcher
Downloads weather data for grid locations using official OpenMeteo Python client
"""

import json
import time
from datetime import datetime
import os
import openmeteo_requests
import requests_cache
from retry_requests import retry

from weather_repository import (
    get_grid_metadata,
    save_grid_metadata,
    save_grid_weather_data,
)


def load_grid_coordinates():
    """Load grid coordinates from MongoDB metadata with JSON fallback"""
    try:
        metadata = get_grid_metadata()
    except Exception as exc:
        print(f"Error loading grid metadata from MongoDB: {exc}")
        metadata = []

    if metadata:
        grid_points = [
            {
                'name': doc.get('name') or f"{float(doc.get('lat', 0.0)):.1f}, {float(doc.get('lon', 0.0)):.1f}",
                'lat': float(doc.get('lat')) if doc.get('lat') is not None else float(doc.get('latitude')),
                'lon': float(doc.get('lon')) if doc.get('lon') is not None else float(doc.get('longitude')),
            }
            for doc in metadata
            if (doc.get('lat') is not None or doc.get('latitude') is not None)
            and (doc.get('lon') is not None or doc.get('longitude') is not None)
        ]
        print(f"Loaded {len(grid_points)} grid points from MongoDB grid_metadata collection")
        return grid_points

    try:
        with open('gridData_1degree.json', 'r', encoding='utf-8') as file:
            content = file.read()

            # Find the JSON part (remove any extra content)
            start = content.find('{')
            brace_count = 0
            end = start
            for i, char in enumerate(content[start:], start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break

            json_content = content[start:end]
            grid_data = json.loads(json_content)

        latitudes = [float(lat.strip()) for lat in grid_data['latitude'].split(',')]
        longitudes = [float(lon.strip()) for lon in grid_data['longitude'].split(',')]

        min_length = min(len(latitudes), len(longitudes))
        latitudes = latitudes[:min_length]
        longitudes = longitudes[:min_length]

        grid_points = []
        metadata_docs = []
        for i in range(len(latitudes)):
            name = f"{latitudes[i]:.1f}, {longitudes[i]:.1f}"
            grid_points.append({'name': name, 'lat': latitudes[i], 'lon': longitudes[i]})
            metadata_docs.append({'name': name, 'lat': latitudes[i], 'lon': longitudes[i]})

        print(
            f"Loaded {len(grid_points)} grid points from gridData_1degree.json (1-degree resolution); seeding MongoDB metadata."
        )
        if metadata_docs:
            try:
                save_grid_metadata(metadata_docs)
            except Exception as exc:
                print(f"Failed to save grid metadata to MongoDB: {exc}")

        return grid_points
    except Exception as e:
        print(f"Error loading 1-degree grid coordinates: {e}")
        print("Creating fallback 1-degree grid data...")
        grid_points = []
        metadata_docs = []
        for lat in range(-11, 7):
            for lon in range(95, 142):
                name = f"{lat}.0, {lon}.0"
                grid_points.append({'name': name, 'lat': float(lat), 'lon': float(lon)})
                metadata_docs.append({'name': name, 'lat': float(lat), 'lon': float(lon)})
        if metadata_docs:
            try:
                save_grid_metadata(metadata_docs)
            except Exception as exc:
                print(f"Failed to save fallback grid metadata to MongoDB: {exc}")
        print(f"Created {len(grid_points)} fallback 1-degree grid points")
        return grid_points


def setup_openmeteo_client():
    """Setup OpenMeteo client with caching and retry mechanism"""
    # Setup cache session (1 hour cache)
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    return openmeteo

def fetch_weather_data(openmeteo_client, locations):
    """Fetch weather data using OpenMeteo client"""
    if not locations:
        return []
    
    # Prepare coordinates for API call
    lats = [loc['lat'] for loc in locations]
    lons = [loc['lon'] for loc in locations]
    
    # API parameters
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lats,
        "longitude": lons,
        "current": ["temperature_2m", "relative_humidity_2m", "weather_code", "wind_speed_10m", "wind_direction_10m"],
        "timezone": "Asia/Jakarta"
    }
    
    try:
        print(f"Fetching weather data for {len(locations)} locations...")
        responses = openmeteo_client.weather_api(url, params=params)
        
        processed_data = []
        
        for i, response in enumerate(responses):
            if i < len(locations):
                location = locations[i]
                
                # Get current weather data
                current = response.Current()
                
                # Extract current weather variables using positional access
                # Variables are returned in the same order as requested in params
                current_vars = {}
                
                if current.VariablesLength() > 0:
                    # temperature_2m (first variable)
                    if current.VariablesLength() > 0:
                        temp_var = current.Variables(0)
                        current_vars['temperature_2m'] = temp_var.Value()
                    
                    # relative_humidity_2m (second variable)
                    if current.VariablesLength() > 1:
                        humidity_var = current.Variables(1)
                        current_vars['relative_humidity_2m'] = humidity_var.Value()
                    
                    # weather_code (third variable)
                    if current.VariablesLength() > 2:
                        weather_var = current.Variables(2)
                        current_vars['weather_code'] = weather_var.Value()
                    
                    # wind_speed_10m (fourth variable)
                    if current.VariablesLength() > 3:
                        wind_speed_var = current.Variables(3)
                        current_vars['wind_speed_10m'] = wind_speed_var.Value()
                    
                    # wind_direction_10m (fifth variable)
                    if current.VariablesLength() > 4:
                        wind_dir_var = current.Variables(4)
                        current_vars['wind_direction_10m'] = wind_dir_var.Value()
                
                processed_location = {
                    'name': location['name'],
                    'lat': location['lat'],
                    'lon': location['lon'],
                    'coordinates': {
                        'latitude': float(response.Latitude()),
                        'longitude': float(response.Longitude()),
                        'elevation': float(response.Elevation())
                    },
                    'weather_data': {
                        'temperature_2m': float(current_vars.get('temperature_2m')) if current_vars.get('temperature_2m') is not None else None,
                        'relative_humidity_2m': float(current_vars.get('relative_humidity_2m')) if current_vars.get('relative_humidity_2m') is not None else None,
                        'weather_code': int(current_vars.get('weather_code')) if current_vars.get('weather_code') is not None else None,
                        'wind_speed_10m': float(current_vars.get('wind_speed_10m')) if current_vars.get('wind_speed_10m') is not None else None,
                        'wind_direction_10m': float(current_vars.get('wind_direction_10m')) if current_vars.get('wind_direction_10m') is not None else None,
                        'timestamp': int(current.Time()) if current.Time() is not None else None,
                        'timezone': str(response.Timezone()).replace("b'", "").replace("'", "") if response.Timezone() is not None else None,
                        'utc_offset_seconds': int(response.UtcOffsetSeconds()) if response.UtcOffsetSeconds() is not None else None,
                        'fetched_at': datetime.now().isoformat()
                    }
                }
                
                processed_data.append(processed_location)
        
        print(f"Successfully processed {len(processed_data)} locations")
        return processed_data
        
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return []

def fetch_weather_data_batched(openmeteo_client, locations, batch_size=50):
    """Fetch weather data in batches to avoid URL length limits"""
    if not locations:
        return []
    
    total_batches = (len(locations) + batch_size - 1) // batch_size
    
    print(f"Processing {len(locations)} locations in batches of {batch_size}...")
    print(f"Total batches: {total_batches}")
    print(f"Estimated time: {total_batches * 10} seconds (with delays)")
    print("=" * 60)
    
    all_processed_data = []
    start_time = time.time()
    
    for batch_num in range(total_batches):
        batch_start_time = time.time()
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(locations))
        batch_locations = locations[start_idx:end_idx]
        
        print(f"\nBatch {batch_num + 1}/{total_batches} ({len(batch_locations)} locations)...")
        
        # Retry logic for failed batches
        max_retries = 3
        retry_delay = 60  # Start with 60 seconds delay
        
        for retry in range(max_retries):
            try:
                batch_data = fetch_weather_data(openmeteo_client, batch_locations)
                if batch_data:
                    all_processed_data.extend(batch_data)
                    batch_time = time.time() - batch_start_time
                    total_time = time.time() - start_time
                    avg_time_per_batch = total_time / (batch_num + 1)
                    remaining_batches = total_batches - (batch_num + 1)
                    eta = remaining_batches * avg_time_per_batch
                    
                    print(f"✅ Batch {batch_num + 1} completed: {len(batch_data)} locations processed")
                    print(f"   Batch time: {batch_time:.1f}s | Total time: {total_time:.1f}s | ETA: {eta:.1f}s")
                    break
                else:
                    print(f"❌ Batch {batch_num + 1} failed (attempt {retry + 1}/{max_retries})")
            except Exception as e:
                error_msg = str(e)
                if "rate limit" in error_msg.lower() or "minutely" in error_msg.lower():
                    print(f"⏳ Rate limit hit for batch {batch_num + 1}. Waiting {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"❌ Error in batch {batch_num + 1}: {e}")
                
                if retry == max_retries - 1:
                    print(f"❌ Batch {batch_num + 1} failed after {max_retries} attempts")
                continue
        
        # Wait between batches to be respectful to the API
        if batch_num < total_batches - 1:
            wait_time = 5  # Increased delay between batches
            print(f"⏸️  Waiting {wait_time} seconds before next batch...")
            time.sleep(wait_time)
    
    total_time = time.time() - start_time
    print(f"\n" + "=" * 60)
    print(f"🎉 Completed all batches in {total_time:.1f} seconds!")
    print(f"📊 Total locations processed: {len(all_processed_data)}/{len(locations)}")
    print(f"📈 Success rate: {(len(all_processed_data)/len(locations)*100):.1f}%")
    return all_processed_data

def main():
    """Main function to fetch and save grid weather data"""
    print("OpenMeteo Grid Weather Data Fetcher (Official Client)")
    print("=" * 60)
    print("Using 1-degree grid resolution for higher detail")
    print("=" * 60)
    
    # Setup OpenMeteo client
    print("Setting up OpenMeteo client with caching...")
    openmeteo_client = setup_openmeteo_client()
    
    # Fetch 1-degree grid weather data
    print("\nFetching 1-degree grid weather data...")
    grid_points = load_grid_coordinates()
    
    if grid_points:
        grid_weather_data = fetch_weather_data_batched(openmeteo_client, grid_points)
        if grid_weather_data:
            save_grid_weather_data(grid_weather_data)
            print(f"Saved {len(grid_weather_data)} grid points to MongoDB grid_weather collection")
        else:
            print("Failed to fetch grid weather data")
    
    print("\nGrid weather data collection complete!")
    print("Grid data stored in MongoDB (grid_weather collection)")
    print("\nCache stored in .cache folder for faster subsequent requests")
    print("\nNote: City weather data is now handled by update_city_weather.py")

if __name__ == "__main__":
    main()