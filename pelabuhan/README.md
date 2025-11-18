# Pelabuhan (Port) Weather Data Collection

This folder contains all port-related weather data collection and processing scripts.

## 📁 File Structure

### Core Scripts
- **`pelabuhan_weather.py`** - Main script to fetch weather data from all ports
- **`create_port_data.py`** - Script to create simplified port data from collected weather data
- **`extract_failed_data.py`** - Script to extract and analyze failed data fetches

### Data Files
- **`pelabuhan_weather_data.json`** - Main weather data collection (large file ~9.9MB)
- **`namaPelabuhan.json`** - Simplified port list with coordinates
- **`failed_port_data.json`** - List of ports with failed data fetches
- **`pelabuhan.json`** - Port coordinate data
- **`cuaca_pelabuhan.py`** - Port weather display script

## 🚀 Usage

### Fetch Fresh Weather Data
```bash
python pelabuhan_weather.py
```

### Extract Failed Data
```bash
python extract_failed_data.py
```

### Create Simplified Port Data
```bash
python create_port_data.py
```

## 📊 Data Structure

### pelabuhan_weather_data.json
Contains detailed weather data for each port including:
- Temperature, humidity, wind speed/direction
- Wave height and classification
- Current speed and direction
- Weather conditions and timestamps

### namaPelabuhan.json
Simplified port data with:
- Port name and slug
- Latitude and longitude coordinates
- Basic port information

## 🔗 Dependencies
- `requests` - HTTP requests to BMKG API
- `json` - JSON data processing
- `datetime` - Timestamp handling
- `re` - Regular expressions for data parsing

## 📝 Notes
- All file paths in scripts are relative to this folder
- Data files are large and should be handled carefully
- Failed data extraction helps identify problematic ports
- Simplified data is used for map display and basic operations 