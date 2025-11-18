# Daily Weather Data Updates

This system automatically keeps your weather data current by checking and updating `pelabuhan/pelabuhan_weather_data.json` daily.

## 📁 Files Created

- `update_weather_data.py` - Main update checker script
- `scheduled_update.py` - Scheduled update script with logging
- `run_daily_update.bat` - Windows batch file for Task Scheduler
- `weather_update.log` - Log file for update history

## 🔄 How It Works

1. **Data Freshness Check**: Compares file modification time with current time
2. **24-Hour Rule**: Updates data if it's older than 24 hours
3. **Automatic Backup**: Creates timestamped backup before updating
4. **Logging**: Records all update activities

## 🚀 Setup Instructions

### Option 1: Windows Task Scheduler (Recommended)

1. **Open Task Scheduler**:
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create Basic Task**:
   - Click "Create Basic Task" in the right panel
   - Name: "Weather Data Update"
   - Description: "Daily weather data update for port weather map"

3. **Set Trigger**:
   - Choose "Daily"
   - Set start time (e.g., 6:00 AM)
   - Set recurrence: Every 1 day

4. **Set Action**:
   - Choose "Start a program"
   - Program: `cmd.exe`
   - Arguments: `/c "cd /d "C:\path\to\your\project" && run_daily_update.bat"`

5. **Finish Setup**:
   - Review settings and click Finish
   - Right-click the task → Properties → Run whether user is logged on or not

### Option 2: Manual Updates

Run manually when needed:
```bash
python update_weather_data.py
```

### Option 3: Cron Job (Linux/Mac)

Add to crontab:
```bash
# Edit crontab
crontab -e

# Add this line for daily updates at 6 AM
0 6 * * * cd /path/to/your/project && python scheduled_update.py
```

## 📊 Monitoring

### Check Update Status
```bash
python update_weather_data.py
```

### View Logs
```bash
# View recent logs
tail -f weather_update.log

# View all logs
cat weather_update.log
```

### Manual Data Collection
```bash
# Force fresh data collection
python pelabuhan/pelabuhan_weather.py
```

## ⚠️ Important Notes

1. **Internet Required**: Updates require internet connection to fetch BMKG data
2. **API Limits**: BMKG API has rate limits, so updates include delays
3. **Backup Safety**: Old data is automatically backed up before updates
4. **Error Handling**: Failed updates are logged and won't break the system

## 🔧 Troubleshooting

### Update Fails
1. Check internet connection
2. Verify BMKG API is accessible
3. Check `weather_update.log` for error details
4. Try manual update: `python pelabuhan/pelabuhan_weather.py`

### Task Scheduler Issues
1. Ensure Python is in system PATH
2. Use full paths in batch file
3. Run as administrator if needed
4. Check Windows Event Viewer for errors

### Data Quality Issues
1. Check success rate in update logs
2. Review failed ports in `pelabuhan/failed_port_data.json`
3. Verify slug generation is working correctly

## 📈 Success Metrics

- **Target Success Rate**: >85% of ports should have weather data
- **Update Frequency**: Every 24 hours maximum
- **Data Freshness**: Always less than 24 hours old

## 🎯 Benefits

- ✅ Always current weather data
- ✅ Automatic backup protection
- ✅ Detailed logging and monitoring
- ✅ No manual intervention needed
- ✅ Graceful error handling 