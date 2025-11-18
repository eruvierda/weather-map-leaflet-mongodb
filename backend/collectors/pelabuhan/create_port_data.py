import json

def create_simplified_port_data():
    """Convert the collected port weather data into a simplified format for the map"""
    
    try:
        # Load the collected port weather data
        with open('pelabuhan_weather_data.json', 'r', encoding='utf-8') as file:
            port_data = json.load(file)
        
        # Create simplified format similar to namaKota.json
        simplified_ports = {}
        
        for port in port_data:
            if port['status'] == 'success':
                port_name = port['port_name']
                coordinates = port['coordinates']
                
                simplified_ports[port_name] = {
                    'latitude': coordinates['lat'],
                    'longitude': coordinates['lon'],
                    'slug': port['slug']
                }
        
        # Save simplified port data
        with open('namaPelabuhan.json', 'w', encoding='utf-8') as file:
            json.dump(simplified_ports, file, indent=2, ensure_ascii=False)
        
        print(f"Successfully created namaPelabuhan.json with {len(simplified_ports)} ports")
        print(f"File saved as: namaPelabuhan.json")
        
        # Show sample data
        sample_ports = list(simplified_ports.items())[:3]
        print(f"\nSample ports:")
        for name, data in sample_ports:
            print(f"  {name}: ({data['latitude']}, {data['longitude']})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_simplified_port_data() 