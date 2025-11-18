#!/usr/bin/env python3
"""
Scheduled City Weather Update Script
Run this script periodically to keep city weather data current
"""

import sys
import os
import logging
from datetime import datetime

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from update_city_weather import main as update_city_weather

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../scheduled_city_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """Main function for scheduled city weather updates"""
    logger = logging.getLogger(__name__)
    
    logger.info("Starting scheduled city weather data update")
    
    try:
        # Run the city weather update
        update_city_weather()
        
        logger.info("City weather data update completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error during city weather data update: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
