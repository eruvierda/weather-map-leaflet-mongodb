import json
import requests
import time
import re
from typing import Dict, List, Optional

def load_existing_coordinates(filename: str = "namaKota.json") -> Dict:
    """Load existing coordinates from file if it exists."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Warning: {filename} contains invalid JSON. Starting fresh.")
        return {}

def save_coordinates(coordinates: Dict, filename: str = "namaKota.json"):
    """Save coordinates to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(coordinates, f, indent=2, ensure_ascii=False)

def fetch_city_coordinate(city_name: str, admin2: Optional[str] = None) -> Optional[Dict]:
    """Fetch coordinate for a single city from OpenMeteo Geocoding API."""
    base_url = "https://geocoding-api.open-meteo.com/v1/search"
    
    # Build search query
    query = city_name
    if admin2:
        query = f"{city_name}, {admin2}, Indonesia"
    
    params = {
        "name": query,
        "count": 1,
        "language": "en",
        "format": "json"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("results") and len(data["results"]) > 0:
            result = data["results"][0]
            return {
                "name": city_name,
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "country": result.get("country", ""),
                "admin1": result.get("admin1", ""),
                "admin2": result.get("admin2", ""),
                "timezone": result.get("timezone", "")
            }
        else:
            print(f"No coordinates found for: {city_name}")
            return None
            
    except requests.RequestException as e:
        print(f"Error fetching coordinates for {city_name}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {city_name}: {e}")
        return None

def parse_cities_from_list_kota() -> List[Dict]:
    """Parse cities from list_kota.json with improved logic."""
    try:
        with open("list_kota.json", 'r', encoding='utf-8') as f:
            content = f.read()
        
        cities_data = []
        
        # Remove comments and clean up the content
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'cities\s*=\s*\[', '', content)
        content = re.sub(r'\];\s*$', '', content)
        
        # Handle double quotes format: "name": "City"
        double_quote_cities = re.findall(r'"name":\s*"([^"]+)"', content)
        for city_name in double_quote_cities:
            cities_data.append({
                "name": city_name.strip(),
                "admin2": None
            })
        
        # Handle single quotes format: { name: 'City' }
        single_quote_cities = re.findall(r"name:\s*'([^']+)'", content)
        for city_name in single_quote_cities:
            if not any(city['name'] == city_name for city in cities_data):
                cities_data.append({
                    "name": city_name.strip(),
                    "admin2": None
                })
        
        # Handle no-space format: {name:'City'}
        no_space_cities = re.findall(r"name:'([^']+)'", content)
        for city_name in no_space_cities:
            if not any(city['name'] == city_name for city in cities_data):
                cities_data.append({
                    "name": city_name.strip(),
                    "admin2": None
                })
        
        # Now handle admin2 for cities that have it
        # Look for cities with admin2 in single quotes format
        admin2_pattern = r"\{[^}]*name:\s*'([^']+)'[^}]*admin2:\s*'([^']+)'[^}]*\}"
        admin2_matches = re.findall(admin2_pattern, content)
        for city_name, admin2 in admin2_matches:
            # Update existing city entry with admin2
            for city in cities_data:
                if city['name'] == city_name:
                    city['admin2'] = admin2.strip()
                    break
        
        # Also handle admin2 in no-space format
        admin2_no_space_pattern = r"\{[^}]*name:'([^']+)'[^}]*admin2:'([^']+)'[^}]*\}"
        admin2_no_space_matches = re.findall(admin2_no_space_pattern, content)
        for city_name, admin2 in admin2_no_space_matches:
            # Update existing city entry with admin2
            for city in cities_data:
                if city['name'] == city_name:
                    city['admin2'] = admin2.strip()
                    break
        
        return cities_data
        
    except Exception as e:
        print(f"Error parsing list_kota.json: {e}")
        return []

def process_cities_from_list_kota():
    """Process cities from list_kota.json and fetch missing coordinates."""
    
    # Load existing coordinates
    existing_coords = load_existing_coordinates()
    print(f"Loaded {len(existing_coords)} existing coordinates")
    
    # Parse cities from list_kota.json
    cities_data = parse_cities_from_list_kota()
    print(f"Found {len(cities_data)} cities to process")
    
    if not cities_data:
        print("No cities found to process!")
        return
    
    # Display first few cities for verification
    print("Sample cities found:")
    for i, city in enumerate(cities_data[:10]):
        print(f"  {i+1}. {city['name']}" + (f" (admin2: {city['admin2']})" if city['admin2'] else ""))
    if len(cities_data) > 10:
        print(f"  ... and {len(cities_data) - 10} more")
    
    # Process cities
    new_coordinates = 0
    skipped = 0
    
    for city_data in cities_data:
        city_name = city_data["name"]
        admin2 = city_data.get("admin2")
        
        # Check if coordinates already exist
        if city_name in existing_coords:
            print(f"Skipping {city_name} - coordinates already exist")
            skipped += 1
            continue
        
        print(f"Fetching coordinates for: {city_name}")
        coordinates = fetch_city_coordinate(city_name, admin2)
        
        if coordinates:
            existing_coords[city_name] = coordinates
            new_coordinates += 1
            print(f"✓ {city_name}: {coordinates['latitude']:.4f}, {coordinates['longitude']:.4f}")
            
            # Save after each successful fetch to avoid losing progress
            save_coordinates(existing_coords)
            
            # Rate limiting to be respectful to the API
            time.sleep(0.5)
        else:
            print(f"✗ Failed to get coordinates for: {city_name}")
    
    print(f"\nProcessing complete!")
    print(f"New coordinates fetched: {new_coordinates}")
    print(f"Cities skipped (already exist): {skipped}")
    print(f"Total coordinates in database: {len(existing_coords)}")

if __name__ == "__main__":
    process_cities_from_list_kota()
