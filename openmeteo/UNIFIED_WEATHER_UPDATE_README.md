# Unified Weather Data Update System

## Overview
This system provides a unified interface for updating weather data across all three data types: **City Weather**, **Grid Weather**, and **Port Weather**. It offers both interactive and automated modes for flexibility in different use cases.

## 🌟 Features

### **1. Unified Interface**
- **Single Script**: Manage all weather data updates from one place
- **Smart Updates**: Only updates data that needs refreshing
- **Status Monitoring**: Real-time status of all weather data files
- **Comprehensive Logging**: Detailed logs for troubleshooting

### **2. Multiple Update Modes**
- **Interactive Mode**: User-friendly menu system for manual updates
- **Automated Mode**: Non-interactive execution for scheduled tasks
- **Individual Updates**: Update specific weather data types
- **Bulk Updates**: Update all weather data in sequence

### **3. Smart Freshness Checking**
- **City Weather**: 6-hour freshness threshold
- **Grid Weather**: 12-hour freshness threshold  
- **Port Weather**: 6-hour freshness threshold
- **Automatic Detection**: Skips updates for fresh data

## 📁 Files

### **Core Scripts**
- **`update_all_weather.py`** - Interactive unified weather update system
- **`update_all_weather_auto.py`** - Automated unified weather update system
- **`update_city_weather.py`** - Dedicated city weather update (imported)

### **Batch Files (Windows)**
- **`run_unified_weather_update.bat`** - Interactive mode
- **`run_automated_weather_update.bat`** - Automated mode
- **`run_city_weather_update.bat`** - City-only update
- **`run_scheduled_city_update.bat`** - Scheduled city update

### **Log Files**
- **`../unified_weather_update.log`** - Interactive mode logs
- **`../automated_weather_update.log`** - Automated mode logs
- **`../city_weather_update.log`** - City update logs

## 🚀 Usage

### **Interactive Mode (Manual Use)**
```bash
cd openmeteo/
python update_all_weather.py
```

**Menu Options:**
1. **Update City Weather Data** - Update only city weather
2. **Update Grid Weather Data** - Update only grid weather  
3. **Update Port Weather Data** - Update only port weather
4. **Update All Weather Data** - Update all weather types
5. **Show Data Status** - Display current status of all data
6. **Exit** - Close the system

### **Automated Mode (Scheduled Use)**
```bash
cd openmeteo/
python update_all_weather_auto.py
```

**Features:**
- No user interaction required
- Updates all weather data automatically
- Returns exit codes for automation systems
- Comprehensive logging for monitoring

### **Windows Batch Files**
```cmd
# Interactive mode
run_unified_weather_update.bat

# Automated mode  
run_automated_weather_update.bat

# City-only update
run_city_weather_update.bat
```

## ⚙️ Configuration

### **Update Thresholds**
```python
# City Weather: 6 hours
if file_age_hours > 6:  # Update needed

# Grid Weather: 12 hours  
if file_age_hours > 12:  # Update needed

# Port Weather: 6 hours
if file_age_hours > 6:  # Update needed
```

### **File Paths**
- **City Data**: `city_weather_data.json` (current directory)
- **Grid Data**: `grid_weather_data_1degree.json` (current directory)
- **Port Data**: `../pelabuhan/pelabuhan_weather_data.json` (relative path)

### **Logging Configuration**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../unified_weather_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
```

## 📊 Status Monitoring

### **Data Freshness Indicators**
- **✅ Fresh**: Data is within freshness threshold
- **❌ Needs Update**: Data exceeds freshness threshold
- **❌ File Not Found**: Data file doesn't exist

### **Update Success Indicators**
- **✅ Success**: Update completed successfully
- **❌ Failed**: Update failed (check logs for details)

### **Example Status Report**
```
============================================================
Weather Data Status Report
============================================================
City Weather: ✅ Fresh (Age: 2.3 hours)
Grid Weather: ❌ Needs Update (Age: 15.7 hours)
Port Weather: ✅ Fresh (Age: 1.8 hours)
============================================================
```

## 🔄 Update Process

### **City Weather Update**
1. Check data freshness (6-hour threshold)
2. Load city coordinates from `namaKota.json`
3. Fetch weather data from OpenMeteo API
4. Save to `city_weather_data.json`
5. Create timestamped backup

### **Grid Weather Update**
1. Check data freshness (12-hour threshold)
2. Execute `fetch_weather_data.py` script
3. Process 1-degree grid coordinates
4. Fetch weather data in batches
5. Save to `grid_weather_data_1degree.json`

### **Port Weather Update**
1. Check data freshness (6-hour threshold)
2. Execute `pelabuhan_weather.py` script
3. Fetch port weather data from BMKG
4. Save to `pelabuhan_weather_data.json`

## 📅 Scheduling

### **Windows Task Scheduler**
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., every 6 hours)
4. Action: Start a program
5. Program: `run_automated_weather_update.bat`
6. Start in: `D:\path\to\leaflet_weather\openmeteo\`

### **Cron (Linux/Mac)**
```bash
# Update every 6 hours
0 */6 * * * cd /path/to/leaflet_weather/openmeteo && python update_all_weather_auto.py

# Update every 4 hours (more frequent)
0 */4 * * * cd /path/to/leaflet_weather/openmeteo && python update_all_weather_auto.py
```

### **Recommended Frequencies**
- **City Weather**: Every 4-6 hours
- **Grid Weather**: Every 8-12 hours
- **Port Weather**: Every 4-6 hours
- **All Data**: Every 6 hours (comprehensive update)

## 🛠️ Troubleshooting

### **Common Issues**

1. **"Port weather script not found"**
   - Verify `pelabuhan/pelabuhan_weather.py` exists
   - Check file paths in the script

2. **"Grid weather update failed"**
   - Check `fetch_weather_data.py` dependencies
   - Verify OpenMeteo API access
   - Check rate limits

3. **"City weather update failed"**
   - Verify `namaKota.json` exists and is valid
   - Check OpenMeteo API connectivity
   - Verify Python dependencies

### **Performance Optimization**
- **Parallel Updates**: Consider running individual updates in parallel
- **Cache Management**: Clear `.cache` folder periodically
- **Log Rotation**: Implement log rotation for long-running systems

### **Error Handling**
- **Retry Logic**: Built-in retry mechanisms for API calls
- **Graceful Degradation**: Continues with other updates if one fails
- **Detailed Logging**: Comprehensive error reporting for debugging

## 🔗 Integration

### **With Main Weather Map**
The `gis_cuaca.html` file automatically loads:
- **City Weather**: `openmeteo/city_weather_data.json`
- **Grid Weather**: `openmeteo/grid_weather_data_1degree.json`
- **Port Weather**: `pelabuhan/pelabuhan_weather_data.json`

### **With Other Systems**
- **Individual Scripts**: Can still run independently
- **Scheduled Tasks**: Integrates with Windows Task Scheduler and cron
- **Monitoring Systems**: Exit codes and logs for external monitoring

## 📈 Monitoring and Maintenance

### **Regular Tasks**
1. **Monitor Logs**: Check for errors or warnings
2. **Verify Data Freshness**: Ensure updates are running on schedule
3. **Check File Sizes**: Monitor data file growth
4. **Clean Old Backups**: Remove old backup files periodically

### **Health Checks**
- **Data Age**: Verify data is within freshness thresholds
- **File Integrity**: Check JSON files are valid
- **Update Success Rate**: Monitor successful vs. failed updates
- **Performance Metrics**: Track update duration and resource usage

### **Backup Strategy**
- **Automatic Backups**: Timestamped backups before updates
- **Manual Backups**: Copy data files to safe location
- **Version Control**: Consider committing data files to git

## 🎯 Use Cases

### **Development Environment**
- **Interactive Mode**: Manual testing and debugging
- **Individual Updates**: Test specific weather data types
- **Status Monitoring**: Verify data freshness during development

### **Production Environment**
- **Automated Mode**: Scheduled updates via task scheduler
- **Bulk Updates**: Comprehensive data refresh
- **Monitoring**: Automated health checks and alerting

### **Maintenance Operations**
- **Data Refresh**: Force updates of stale data
- **System Recovery**: Restore weather data after failures
- **Performance Tuning**: Optimize update schedules

---

## 📋 Quick Start Guide

1. **Navigate to openmeteo folder**
   ```bash
   cd openmeteo/
   ```

2. **Run interactive mode**
   ```bash
   python update_all_weather.py
   ```

3. **Choose update option**
   - Option 4: Update all weather data
   - Option 5: Check current status

4. **For automated use**
   ```bash
   python update_all_weather_auto.py
   ```

---

*Last Updated: December 2024*
*Version: 2.0 - Unified System*
