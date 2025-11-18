import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PEL_DIR = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from openmeteo.weather_repository import (
    get_port_metadata,
    save_port_metadata,
    save_port_weather_data,
)


def _load_ports_from_mongo():
    try:
        metadata = get_port_metadata()
    except Exception as exc:
        print(f"Error loading port metadata from MongoDB: {exc}")
        metadata = []

    if not metadata:
        return []

    ports = []
    for doc in metadata:
        lat = doc.get('lat') or doc.get('latitude')
        lon = doc.get('lon') or doc.get('longitude')
        if lat is None or lon is None:
            continue
        name = doc.get('port_name') or doc.get('name')
        slug = doc.get('slug') or create_slug(name or '')
        ports.append(
            {
                'id': doc.get('id') or doc.get('slug') or f"PORT_{len(ports)+1:03d}",
                'name': name,
                'lat': float(lat),
                'lon': float(lon),
                'slug': slug,
            }
        )

    print(f"Loaded {len(ports)} ports from MongoDB port_metadata collection")
    return ports


def _load_ports_from_json():
    possible_paths = [
        PEL_DIR / 'pelabuhan.json',
        PROJECT_ROOT / 'pelabuhan' / 'pelabuhan.json',
        Path('pelabuhan.json'),
    ]

    data = None
    used_path = None
    for path in possible_paths:
        if path.exists():
            with path.open('r', encoding='utf-8') as file:
                data = json.load(file)
                used_path = path
                break

    if data is None:
        print("Error: Could not find pelabuhan.json in any known locations.")
        return []

    print(f"Loaded data from: {used_path}")

    ports = []
    metadata_docs = []
    for i, item in enumerate(data):
        if isinstance(item, str) and 'Pelabuhan' in item:
            if i + 2 < len(data):
                lat = data[i + 1]
                lon = data[i + 2]
                if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                    slug = create_slug(item)
                    ports.append(
                        {
                            'id': f"PORT_{len(ports)+1:03d}",
                            'name': item,
                            'lat': float(lat),
                            'lon': float(lon),
                            'slug': slug,
                        }
                    )
                    metadata_docs.append(
                        {
                            'slug': slug,
                            'port_name': item,
                            'lat': float(lat),
                            'lon': float(lon),
                        }
                    )

    if metadata_docs:
        print(
            f"Loaded {len(ports)} ports from pelabuhan.json; seeding MongoDB port_metadata collection."
        )
        try:
            save_port_metadata(metadata_docs)
        except Exception as exc:
            print(f"Failed to save port metadata to MongoDB: {exc}")

    return ports


def load_pelabuhan_data():
    ports = _load_ports_from_mongo()
    if ports:
        return ports
    return _load_ports_from_json()


def create_slug(port_name):
    """Convert port name to slug for BMKG API"""
    # Convert to lowercase and replace non-alphanumeric characters with hyphens
    slug = re.sub(r'[^a-zA-Z0-9\s]', ' ', port_name)
    slug = re.sub(r'\s+', '-', slug.strip()).lower()
    return slug


def fetch_port_weather(port_name, port_lat, port_lon, slug=None):
    """Fetch weather data for a port"""
    try:
        slug = slug or create_slug(port_name)
        api_url = f"https://maritim.bmkg.go.id/api/pelabuhan?slug={slug}"

        print(f"Fetching: {port_name} -> {slug}")

        response = requests.get(api_url, timeout=30)

        if response.status_code == 200:
            weather_data = response.json()
            return {
                'port_name': port_name,
                'slug': slug,
                'coordinates': {'lat': port_lat, 'lon': port_lon},
                'weather_data': weather_data,
                'fetched_at': datetime.utcnow().isoformat(),
                'status': 'success'
            }
        else:
            return {
                'port_name': port_name,
                'slug': slug,
                'coordinates': {'lat': port_lat, 'lon': port_lon},
                'weather_data': None,
                'fetched_at': datetime.utcnow().isoformat(),
                'status': 'failed',
                'error': f"HTTP {response.status_code}"
            }

    except Exception as e:
        return {
            'port_name': port_name,
            'slug': slug or create_slug(port_name),
            'coordinates': {'lat': port_lat, 'lon': port_lon},
            'weather_data': None,
            'fetched_at': datetime.utcnow().isoformat(),
            'status': 'error',
            'error': str(e)
        }


def main():
    print("Port Weather Data Fetcher")
    print("=" * 50)

    ports = load_pelabuhan_data()
    if not ports:
        print("No ports found. Exiting.")
        return

    print(f"Found {len(ports)} ports to process")
    print("Estimated time: ~5-6 minutes (with 500ms delays)")
    print("Starting data collection...\n")

    results = []
    successful = 0
    failed = 0

    # Process all ports
    for i, port in enumerate(ports, 1):
        print(f"[{i:3d}/{len(ports)}] Processing: {port['name']}")

        result = fetch_port_weather(port['name'], port['lat'], port['lon'], port.get('slug'))

        results.append(result)

        if result['status'] == 'success':
            successful += 1
            print(f"    Success")
        else:
            failed += 1
            print(f"    Failed: {result.get('error', 'Unknown error')}")
        
        # Progress update every 50 ports
        if i % 50 == 0:
            print(f"\nProgress: {i}/{len(ports)} ({i/len(ports)*100:.1f}%)")
            print(f"   Successful: {successful}, Failed: {failed}\n")
        
        # Add delay to avoid overwhelming BMKG API
        import time
        time.sleep(0.5)  # 500ms delay between requests
    
    # Final summary
    print("\n" + "=" * 50)
    print("FINAL RESULTS")
    print("=" * 50)
    print(f"Total ports processed: {len(ports)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/len(ports)*100:.1f}%")
    
    # Save results to MongoDB
    try:
        save_port_weather_data(results)
        print(f"\nSaved {len(results)} port entries to MongoDB port_weather collection")
    except Exception as e:
        print(f"\n❌ Failed to save port data to MongoDB: {e}")
    
    if successful > 0:
        print(f"\nReady to integrate {successful} ports into your weather map!")
    else:
        print(f"\nNo successful data collected. Check your internet connection and API status.")


if __name__ == "__main__":
    main()