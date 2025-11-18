import json

def extract_failed_data():
    """Extract all failed data fetches from pelabuhan_weather_data.json"""
    
    try:
        # Load the collected port weather data
        with open('pelabuhan_weather_data.json', 'r', encoding='utf-8') as file:
            port_data = json.load(file)
        
        # Filter failed entries
        failed_data = []
        
        for port in port_data:
            if port['status'] == 'failed':
                failed_data.append({
                    'port_name': port.get('port_name', 'Unknown'),
                    'slug': port.get('slug', 'Unknown'),
                    'coordinates': port.get('coordinates', {}),
                    'error_message': port.get('error_message', 'No error message'),
                    'timestamp': port.get('timestamp', 'Unknown')
                })
        
        # Save failed data to separate file
        with open('failed_port_data.json', 'w', encoding='utf-8') as file:
            json.dump(failed_data, file, indent=2, ensure_ascii=False)
        
        print(f"Found {len(failed_data)} failed data fetches")
        print(f"Failed data saved to: failed_port_data.json")
        
        # Show summary of failed ports
        print(f"\nFailed ports summary:")
        for failed in failed_data[:10]:  # Show first 10
            print(f"  {failed['port_name']}: {failed['error_message']}")
        
        if len(failed_data) > 10:
            print(f"  ... and {len(failed_data) - 10} more failed entries")
            
        # Show error types
        error_types = {}
        for failed in failed_data:
            error_msg = failed['error_message']
            error_types[error_msg] = error_types.get(error_msg, 0) + 1
        
        print(f"\nError types breakdown:")
        for error_msg, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_msg}: {count} occurrences")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_failed_data() 