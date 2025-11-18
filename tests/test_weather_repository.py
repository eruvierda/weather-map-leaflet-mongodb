"""Unit tests for the MongoDB weather repository helpers."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import sys
import unittest
from unittest.mock import patch

import mongomock

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.data import weather_repository as repo


class WeatherRepositoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.mongo_client = mongomock.MongoClient()
        self.get_client_patcher = patch(
            "backend.data.weather_repository._get_client",
            return_value=self.mongo_client,
        )
        self.get_client_patcher.start()
        repo._CLIENT = None  # ensure repository rebuilds the client with the mock

        database = self.mongo_client[repo._get_db_name()]
        for collection_name in ("city_weather", "grid_weather", "port_weather"):
            database[collection_name].delete_many({})

    def tearDown(self) -> None:
        self.get_client_patcher.stop()
        repo._CLIENT = None

    def test_save_city_weather_data_upserts_by_name(self) -> None:
        collection = self.mongo_client[repo._get_db_name()]["city_weather"]

        repo.save_city_weather_data([self._city_doc("Test City", temperature=25.5)])
        self.assertEqual(collection.count_documents({}), 1)

        # Updating the same city should upsert instead of creating duplicates
        repo.save_city_weather_data([self._city_doc("Test City", temperature=27.0)])
        self.assertEqual(collection.count_documents({}), 1)

        stored = collection.find_one({"name": "Test City"})
        self.assertAlmostEqual(stored["weather_data"]["temperature_2m"], 27.0)
        self.assertIn("updated_at", stored)

    def test_save_grid_weather_data_replaces_collection(self) -> None:
        collection = self.mongo_client[repo._get_db_name()]["grid_weather"]
        collection.insert_one({"name": "stale"})

        repo.save_grid_weather_data(
            [self._grid_doc("G1"), self._grid_doc("G2", latitude=2.0, longitude=3.0)]
        )

        names = sorted(doc["name"] for doc in collection.find({}))
        self.assertEqual(names, ["G1", "G2"])
        self.assertEqual(collection.count_documents({}), 2)

    def test_save_port_weather_data_upserts_by_slug(self) -> None:
        collection = self.mongo_client[repo._get_db_name()]["port_weather"]

        repo.save_port_weather_data([self._port_doc("Port Sample", slug="port-sample")])
        self.assertEqual(collection.count_documents({}), 1)

        updated = self._port_doc("Port Sample", slug="port-sample")
        updated["weather_data"]["issued"] = "2025-11-17 00:00 UTC"
        repo.save_port_weather_data([updated])

        stored = collection.find_one({"slug": "port-sample"})
        self.assertEqual(stored["weather_data"]["issued"], "2025-11-17 00:00 UTC")
        self.assertEqual(collection.count_documents({}), 1)

    def test_is_city_weather_fresh_checks_latest_timestamp(self) -> None:
        collection = self.mongo_client[repo._get_db_name()]["city_weather"]
        stale_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        collection.insert_one(self._city_doc("Stale City", fetched_at=stale_time))
        self.assertFalse(repo.is_city_weather_fresh(max_age_hours=6))

        collection.delete_many({})
        fresh_time = datetime.now(timezone.utc).isoformat()
        collection.insert_one(self._city_doc("Fresh City", fetched_at=fresh_time))
        self.assertTrue(repo.is_city_weather_fresh(max_age_hours=6))

    @staticmethod
    def _city_doc(
        name: str,
        temperature: float = 26.0,
        fetched_at: Optional[str] = None,
    ) -> dict:
        if fetched_at is None:
            fetched_at = datetime.now(timezone.utc).isoformat()
        return {
            "name": name,
            "lat": 1.23,
            "lon": 4.56,
            "coordinates": {
                "latitude": 1.23,
                "longitude": 4.56,
                "elevation": 10.0,
            },
            "weather_data": {
                "temperature_2m": temperature,
                "relative_humidity_2m": 70.0,
                "weather_code": 2,
                "wind_speed_10m": 5.5,
                "wind_direction_10m": 120.0,
                "timestamp": int(datetime.now().timestamp()),
                "timezone": "Asia/Jakarta",
                "utc_offset_seconds": 25200,
                "fetched_at": fetched_at,
            },
        }

    @staticmethod
    def _grid_doc(
        name: str,
        latitude: float = -11.0,
        longitude: float = 95.0,
        temperature: float = 27.0,
    ) -> dict:
        return {
            "name": name,
            "lat": latitude,
            "lon": longitude,
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude,
                "elevation": 0.0,
            },
            "weather_data": {
                "temperature_2m": temperature,
                "relative_humidity_2m": 80.0,
                "weather_code": 1,
                "wind_speed_10m": 12.5,
                "wind_direction_10m": 45.0,
                "timestamp": int(datetime.now().timestamp()),
                "timezone": "Asia/Jakarta",
                "utc_offset_seconds": 25200,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    @staticmethod
    def _port_doc(name: str, slug: str) -> dict:
        return {
            "port_name": name,
            "slug": slug,
            "coordinates": {"lat": -6.2, "lon": 106.8},
            "weather_data": {
                "code": "XP001",
                "issued": "2025-11-16 00:00 UTC",
            },
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "status": "success",
        }


if __name__ == "__main__":
    unittest.main()
