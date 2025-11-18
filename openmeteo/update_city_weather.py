#!/usr/bin/env python3
"""
City Weather Update Script
Updates city weather data using OpenMeteo API
Run this script periodically to keep city weather data current
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path to import local modules
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR))

import openmeteo_requests
import requests_cache
from retry_requests import retry

from weather_repository import (
    get_city_metadata,
    is_city_weather_fresh,
    save_city_metadata,
    save_city_weather_data,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(str((SCRIPT_DIR.parent / 'city_weather_update.log').resolve())),
        logging.StreamHandler(sys.stdout)
    ]
)

def load_city_coordinates():
    """Load city coordinates from MongoDB metadata, falling back to namaKota.json"""
    try:
        metadata = get_city_metadata()
    except Exception as exc:
        logging.error(f"Error loading city metadata from MongoDB: {exc}")
        metadata = []

    if metadata:
        cities = [
            {
                'name': doc.get('name'),
                'lat': doc.get('latitude'),
                'lon': doc.get('longitude'),
            }
            for doc in metadata
            if doc.get('latitude') is not None and doc.get('longitude') is not None
        ]
        logging.info(f"Loaded {len(cities)} cities from MongoDB city_metadata collection")
        return cities

    # Fallback to local JSON seed file
    try:
        coordinates_path = SCRIPT_DIR / 'namaKota.json'
        with coordinates_path.open('r', encoding='utf-8') as file:
            city_data = json.load(file)

        cities = []
        metadata_docs = []
        for city_name, data in city_data.items():
            lat = data.get('latitude')
            lon = data.get('longitude')
            if lat is None or lon is None:
                continue
            cities.append({'name': city_name, 'lat': lat, 'lon': lon})
            document = dict(data)
            document.setdefault('name', city_name)
            metadata_docs.append(document)

        logging.info(
            f"Loaded {len(cities)} cities from {coordinates_path}; seeding MongoDB metadata."
        )
        if metadata_docs:
            try:
                save_city_metadata(metadata_docs)
            except Exception as exc:
                logging.error(f"Failed to save city metadata to MongoDB: {exc}")

        return cities
    except Exception as e:
        logging.error(f"Error loading city coordinates: {e}")
        return []

def setup_openmeteo_client():
    """Setup OpenMeteo client with caching and retry mechanism"""
    # Setup cache session (1 hour cache)
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    return openmeteo

def fetch_city_weather_data(openmeteo_client, cities):
    """Fetch weather data for cities using OpenMeteo client"""
    if not cities:
        return []
    
    # Prepare coordinates for API call
    lats = [city['lat'] for city in cities]
    lons = [city['lon'] for city in cities]
    
    # API parameters
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lats,
        "longitude": lons,
        "current": ["temperature_2m", "relative_humidity_2m", "weather_code", "wind_speed_10m", "wind_direction_10m"],
        "timezone": "Asia/Jakarta"
    }
    
    try:
        logging.info(f"Fetching weather data for {len(cities)} cities...")
        responses = openmeteo_client.weather_api(url, params=params)
        
        processed_data = []
        
        for i, response in enumerate(responses):
            if i < len(cities):
                city = cities[i]
                
                # Get current weather data
                current = response.Current()
                
                # Extract current weather variables using positional access
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
                
                processed_city = {
                    'name': city['name'],
                    'lat': city['lat'],
                    'lon': city['lon'],
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
                
                processed_data.append(processed_city)
        
        logging.info(f"Successfully processed {len(processed_data)} cities")
        return processed_data
        
    except Exception as e:
        logging.error(f"Error fetching city weather data: {e}")
        return []

def check_data_freshness():
    """Check if the city weather data in MongoDB is fresh (less than 6 hours old)."""
    try:
        fresh = is_city_weather_fresh()
        if fresh:
            logging.info("Most recent city weather data in MongoDB is still fresh (<= 6 hours old).")
        else:
            logging.info("City weather data in MongoDB is stale or missing. Update required.")
        return fresh
    except Exception as e:
        logging.error(f"Error checking MongoDB data freshness: {e}")
        return False

def main():
    """Main function to update city weather data"""
    logger = logging.getLogger(__name__)
    
    logger.info("Starting city weather data update")
    logger.info("=" * 60)
    
    # Check if update is needed
    if check_data_freshness():
        logger.info("City weather data is still fresh. No update needed.")
        return 0
    
    try:
        # Setup OpenMeteo client
        logger.info("Setting up OpenMeteo client with caching...")
        openmeteo_client = setup_openmeteo_client()
        
        # Load city coordinates
        logger.info("Loading city coordinates...")
        cities = load_city_coordinates()
        
        if not cities:
            logger.error("No cities loaded. Cannot proceed with update.")
            return 1
        
        # Fetch city weather data
        logger.info(f"Fetching weather data for {len(cities)} cities...")
        city_weather_data = fetch_city_weather_data(openmeteo_client, cities)
        
        if city_weather_data:
            # Save the updated data to MongoDB
            save_city_weather_data(city_weather_data)
            logger.info("City weather data update completed successfully!")
            
            # Log summary
            logger.info(f"Updated {len(city_weather_data)} cities")
            logger.info("Data saved to MongoDB city_weather collection")
            
            return 0
        else:
            logger.error("Failed to fetch city weather data")
            return 1
            
    except Exception as e:
        logger.error(f"Error during city weather data update: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
