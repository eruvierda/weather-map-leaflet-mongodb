import sys
from pathlib import Path

# Ensure project root is importable so we can use shared Mongo helpers
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Add pelabuhan folder to path for imports
PELABUHAN_DIR = Path(__file__).resolve().parent
if str(PELABUHAN_DIR) not in sys.path:
    sys.path.append(str(PELABUHAN_DIR))

from openmeteo.weather_repository import (  # noqa: E402
    get_port_weather_documents,
    is_port_weather_fresh,
)
from pelabuhan_weather import main as collect_weather_data  # noqa: E402


def check_data_freshness(max_age_hours: float = 24) -> bool:
    """Check if port weather data in MongoDB is current."""

    try:
        fresh = is_port_weather_fresh(max_age_hours=max_age_hours)
    except Exception as exc:
        print(f"❌ Failed to check MongoDB freshness: {exc}")
        return False

    if fresh:
        print(f"✅ Port weather data is current (<= {max_age_hours} hours old)")
    else:
        print(f"⚠️  Port weather data is stale (>{max_age_hours} hours). Updating...")
    return fresh


def main():
    """Main function to check and update weather data"""
    print("🌤️  Weather Data Update Checker")
    print("=" * 50)
    
    # Check if data is current
    is_current = check_data_freshness()
    
    if not is_current:
        print("\n🔄 Starting data update process...")
        
        # Collect fresh data
        try:
            collect_weather_data()
            print("\n✅ Weather data updated successfully!")
        except Exception as e:
            print(f"\n❌ Error updating weather data: {e}")
            return False
    else:
        print("\n✅ No update needed. Data is current.")
    
    # Verify the updated data from MongoDB
    try:
        data = get_port_weather_documents()
        total = len(data)
        successful = sum(1 for item in data if item.get('status') == 'success')
        failed = sum(1 for item in data if item.get('status') == 'failed')
        
        print(f"\n📊 Data Summary:")
        print(f"   📈 Total ports: {total}")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        success_rate = (successful / total * 100) if total else 0
        print(f"   📊 Success rate: {success_rate:.1f}%")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not verify MongoDB data: {e}")
    
    return True

if __name__ == "__main__":
    main()