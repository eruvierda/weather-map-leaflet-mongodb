#!/usr/bin/env python3
"""
Scheduled OpenMeteo Weather Data Update Script
Run this script periodically to keep weather data current
"""

import sys
import os
import logging
from datetime import datetime

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_weather_data import main as fetch_weather

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('openmeteo_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """Main function for scheduled OpenMeteo updates"""
    logger = logging.getLogger(__name__)
    
    logger.info("Starting scheduled OpenMeteo weather data update")
    
    try:
        # Run the weather data fetch
        fetch_weather()
        
        logger.info("OpenMeteo weather data update completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error during OpenMeteo weather data update: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 