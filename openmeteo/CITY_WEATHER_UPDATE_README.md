# City Weather Update System

## Overview
This system provides dedicated functionality for updating city weather data using the OpenMeteo API. It's designed to be lightweight, focused, and easily schedulable.

## Files

### **Core Scripts**
- **`update_city_weather.py`** - Main city weather update script
- **`scheduled_city_update.py`** - Wrapper for scheduled execution
- **`fetch_weather_data.py`** - Grid weather data fetcher (city functionality removed)

### **Batch Files (Windows)**
- **`run_city_weather_update.bat`** - Manual city weather update
- **`run_scheduled_city_update.bat`** - Scheduled city weather update

### **Data Files**
- **`namaKota.json`** - City coordinates and names
- **`city_weather_data.json`** - Current city weather data
- **`city_weather_data_backup_YYYYMMDD_HHMMSS.json`** - Timestamped backups

## Features

### **1. Smart Update Logic**
- **Data Freshness Check**: Only updates if data is older than 6 hours
- **Automatic Backup**: Creates timestamped backups before each update
- **Efficient API Usage**: Single batch request for all cities

### **2. Comprehensive Weather Data**
- **Temperature**: 2-meter temperature in Celsius
- **Humidity**: Relative humidity percentage
- **Weather Code**: WMO weather condition codes
- **Wind**: Speed and direction at 10 meters
- **Metadata**: Timestamps, timezone, elevation

### **3. Robust Error Handling**
- **Retry Mechanism**: Automatic retries with exponential backoff
- **Caching**: 1-hour API response caching
- **Logging**: Comprehensive logging to file and console

## Usage

### **Manual Update**
```bash
cd openmeteo/
python update_city_weather.py
```

### **Windows Batch File**
```cmd
cd openmeteo/
run_city_weather_update.bat
```

### **Scheduled Update**
```cmd
cd openmeteo/
run_scheduled_city_update.bat
```

## Configuration

### **Update Frequency**
- **Default**: 6-hour freshness threshold
- **Configurable**: Modify `check_data_freshness()` function
- **Recommended**: Update every 4-6 hours for current data

### **API Parameters**
- **Timezone**: Asia/Jakarta (Indonesia)
- **Weather Variables**: Temperature, humidity, weather code, wind
- **Cache Duration**: 1 hour (configurable in `setup_openmeteo_client()`)

### **Logging**
- **File**: `../city_weather_update.log` (parent directory)
- **Console**: Real-time output
- **Level**: INFO (configurable)

## Data Structure

### **Input: namaKota.json**
```json
{
  "Jakarta": {
    "latitude": -6.2088,
    "longitude": 106.8456
  }
}
```

### **Output: city_weather_data.json**
```json
[
  {
    "name": "Jakarta",
    "lat": -6.2088,
    "lon": 106.8456,
    "coordinates": {
      "latitude": -6.2088,
      "longitude": 106.8456,
      "elevation": 8.0
    },
    "weather_data": {
      "temperature_2m": 28.5,
      "relative_humidity_2m": 75,
      "weather_code": 1,
      "wind_speed_10m": 12.3,
      "wind_direction_10m": 180,
      "timestamp": 1703123456,
      "timezone": "Asia/Jakarta",
      "utc_offset_seconds": 25200,
      "fetched_at": "2023-12-21T10:30:45.123456"
    }
  }
]
```

## Scheduling

### **Windows Task Scheduler**
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., every 4 hours)
4. Action: Start a program
5. Program: `run_scheduled_city_update.bat`
6. Start in: `D:\path\to\leaflet_weather\openmeteo\`

### **Cron (Linux/Mac)**
```bash
# Update every 4 hours
0 */4 * * * cd /path/to/leaflet_weather/openmeteo && python scheduled_city_update.py
```

## Monitoring

### **Log Files**
- **`city_weather_update.log`**: Manual update logs
- **`scheduled_city_update.log`**: Scheduled update logs

### **Success Indicators**
- ✅ "City weather data update completed successfully!"
- ✅ "Updated X cities"
- ✅ "Data saved to city_weather_data.json"

### **Error Indicators**
- ❌ "Error during city weather data update"
- ❌ "Failed to fetch city weather data"
- ❌ "No cities loaded. Cannot proceed with update."

## Dependencies

### **Required Python Packages**
```bash
pip install openmeteo-requests requests-cache retry-requests
```

### **System Requirements**
- Python 3.7+
- Internet connection for API access
- Write permissions for log and data files

## Troubleshooting

### **Common Issues**

1. **"No cities loaded"**
   - Check `namaKota.json` exists and is valid JSON
   - Verify file encoding is UTF-8

2. **"Failed to fetch city weather data"**
   - Check internet connection
   - Verify OpenMeteo API is accessible
   - Check rate limits (1000 requests/day free tier)

3. **"Error saving data"**
   - Verify write permissions in openmeteo folder
   - Check available disk space

### **Performance Optimization**
- **Cache Management**: Clear `.cache` folder if API responses become stale
- **Batch Size**: Cities are processed in a single API call (efficient)
- **Update Frequency**: Balance between data freshness and API usage

## Integration

### **With Main Weather Map**
The `gis_cuaca.html` file automatically loads city weather data from:
```
openmeteo/city_weather_data.json
```

### **With Other Systems**
- **Port Weather**: Independent system in `pelabuhan/` folder
- **Grid Weather**: Handled by `fetch_weather_data.py`
- **Maritime Weather**: Independent system in `maritime_weather/` folder

## Maintenance

### **Regular Tasks**
1. **Monitor Logs**: Check for errors or warnings
2. **Verify Data**: Ensure city weather data is current
3. **Update Coordinates**: Modify `namaKota.json` if city list changes
4. **Clean Cache**: Remove old `.cache` files periodically

### **Backup Strategy**
- **Automatic**: Timestamped backups created before each update
- **Manual**: Copy `city_weather_data.json` to safe location
- **Version Control**: Consider committing data files to git

---

*Last Updated: December 2024*
*Version: 1.0*
