"""MongoDB persistence helpers for weather datasets."""

from __future__ import annotations

import os
from datetime import datetime
from collections.abc import Mapping
from typing import Any, Dict, Iterable, List, Optional

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection

load_dotenv()

_CLIENT: Optional[MongoClient] = None


def _get_client() -> MongoClient:
    global _CLIENT
    if _CLIENT is None:
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        _CLIENT = MongoClient(mongo_uri)
    return _CLIENT


def _get_db_name() -> str:
    return os.getenv("MONGO_DB", "weather_map")


def _get_collection(env_name: str, default: str) -> Collection:
    db = _get_client()[_get_db_name()]
    collection_name = os.getenv(env_name, default)
    return db[collection_name]


def _ensure_iterable(data: Optional[Iterable[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if not data:
        return []
    return list(data)


# ----------------------------- Metadata helpers ------------------------- #


def save_city_metadata(data: Iterable[Dict[str, Any]]) -> None:
    records = _ensure_iterable(data)
    if not records:
        return

    collection = _get_collection("CITY_METADATA_COLLECTION", "city_metadata")
    operations = []
    for record in records:
        document = dict(record)
        name = document.get("name")
        latitude = document.get("latitude")
        longitude = document.get("longitude")
        if not name or latitude is None or longitude is None:
            continue
        document["updated_at"] = datetime.utcnow()
        operations.append(
            UpdateOne({"name": name}, {"$set": document}, upsert=True)
        )

    if operations:
        collection.bulk_write(operations, ordered=False)


def save_grid_metadata(data: Iterable[Dict[str, Any]]) -> None:
    points = _ensure_iterable(data)
    if not points:
        return

    collection = _get_collection("GRID_METADATA_COLLECTION", "grid_metadata")
    documents: List[Dict[str, Any]] = []
    for point in points:
        document = dict(point)
        lat = document.get("lat")
        lon = document.get("lon")
        if lat is None or lon is None:
            continue
        document.setdefault("name", document.get("name") or f"{float(lat):.1f}, {float(lon):.1f}")
        document["updated_at"] = datetime.utcnow()
        documents.append(document)

    if documents:
        collection.delete_many({})
        collection.insert_many(documents, ordered=False)


def save_port_metadata(data: Iterable[Dict[str, Any]]) -> None:
    ports = _ensure_iterable(data)
    if not ports:
        return

    collection = _get_collection("PORT_METADATA_COLLECTION", "port_metadata")
    operations = []
    for port in ports:
        document = dict(port)
        slug = document.get("slug") or document.get("id")
        latitude = document.get("lat")
        longitude = document.get("lon")
        if not slug or latitude is None or longitude is None:
            continue
        document.setdefault("port_name", document.get("port_name") or document.get("name"))
        document["updated_at"] = datetime.utcnow()
        operations.append(
            UpdateOne({"slug": slug}, {"$set": document}, upsert=True)
        )

    if operations:
        collection.bulk_write(operations, ordered=False)


def get_city_metadata() -> List[Dict[str, Any]]:
    collection = _get_collection("CITY_METADATA_COLLECTION", "city_metadata")
    return list(collection.find({}, {"_id": 0}))


def get_grid_metadata() -> List[Dict[str, Any]]:
    collection = _get_collection("GRID_METADATA_COLLECTION", "grid_metadata")
    return list(collection.find({}, {"_id": 0}))


def get_port_metadata() -> List[Dict[str, Any]]:
    collection = _get_collection("PORT_METADATA_COLLECTION", "port_metadata")
    return list(collection.find({}, {"_id": 0}))


# ----------------------------- Save helpers ----------------------------- #


def save_city_weather_data(data: Iterable[Dict[str, Any]]) -> None:
    cities = _ensure_iterable(data)
    if not cities:
        return

    collection = _get_collection("CITY_COLLECTION", "city_weather")
    operations = []
    for city in cities:
        document = dict(city)
        document["updated_at"] = datetime.utcnow()
        operations.append(
            UpdateOne({"name": city.get("name")}, {"$set": document}, upsert=True)
        )

    if operations:
        collection.bulk_write(operations, ordered=False)


def save_grid_weather_data(data: Iterable[Dict[str, Any]]) -> None:
    grid_points = _ensure_iterable(data)
    if not grid_points:
        return

    collection = _get_collection("GRID_COLLECTION", "grid_weather")
    # Replace the collection contents for grid snapshots
    collection.delete_many({})
    for point in grid_points:
        point["updated_at"] = datetime.utcnow()
    collection.insert_many(grid_points, ordered=False)


def save_port_weather_data(data: Iterable[Dict[str, Any]]) -> None:
    ports = _ensure_iterable(data)
    if not ports:
        return

    collection = _get_collection("PORT_COLLECTION", "port_weather")
    operations = []
    for port in ports:
        document = dict(port)
        document.setdefault("slug", port.get("slug"))
        document.setdefault("port_name", port.get("port_name"))
        document["updated_at"] = datetime.utcnow()
        operations.append(
            UpdateOne({"slug": document.get("slug")}, {"$set": document}, upsert=True)
        )

    if operations:
        collection.bulk_write(operations, ordered=False)


# ----------------------------- Fetch helpers ---------------------------- #


def get_city_weather_documents() -> List[Dict[str, Any]]:
    collection = _get_collection("CITY_COLLECTION", "city_weather")
    return list(collection.find({}, {"_id": 0}))


def get_grid_weather_documents() -> List[Dict[str, Any]]:
    collection = _get_collection("GRID_COLLECTION", "grid_weather")
    return list(collection.find({}, {"_id": 0}))


def get_port_weather_documents() -> List[Dict[str, Any]]:
    collection = _get_collection("PORT_COLLECTION", "port_weather")
    return list(collection.find({}, {"_id": 0}))


# ----------------------------- Freshness helpers ------------------------ #


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        if value.endswith("Z"):
            try:
                return datetime.fromisoformat(value[:-1] + "+00:00")
            except ValueError:
                return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None


def _hours_since(dt: Optional[datetime]) -> Optional[float]:
    if dt is None:
        return None
    reference = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    return (reference - dt).total_seconds() / 3600


def _get_latest_timestamp(
    collection: Collection, path: List[str]
) -> Optional[datetime]:
    projection = {"_id": 0}
    for segment in path:
        projection[f"{'.'.join(path)}"] = 1
    sort_field = ".".join(path)
    document = collection.find_one(
        {sort_field: {"$exists": True}},
        sort=[(sort_field, -1)],
        projection={sort_field: 1, "_id": 0},
    )
    if not document:
        return None
    current = document
    for segment in path:
        if isinstance(current, dict):
            current = current.get(segment)
        else:
            return None
    if isinstance(current, str):
        return _parse_iso_datetime(current)
    return None


def get_latest_city_fetch_time() -> Optional[datetime]:
    collection = _get_collection("CITY_COLLECTION", "city_weather")
    return _get_latest_timestamp(collection, ["weather_data", "fetched_at"])


def get_latest_grid_fetch_time() -> Optional[datetime]:
    collection = _get_collection("GRID_COLLECTION", "grid_weather")
    return _get_latest_timestamp(collection, ["weather_data", "fetched_at"])


def get_latest_port_time() -> Optional[datetime]:
    collection = _get_collection("PORT_COLLECTION", "port_weather")
    document = collection.find_one(
        {"fetched_at": {"$exists": True}},
        sort=[("fetched_at", -1)],
        projection={"fetched_at": 1, "_id": 0},
    )
    if not document:
        return None
    return _parse_iso_datetime(document.get("fetched_at"))


def is_city_weather_fresh(max_age_hours: float = 6) -> bool:
    latest = get_latest_city_fetch_time()
    if latest is None:
        return False
    age_hours = _hours_since(latest)
    return age_hours is not None and age_hours <= max_age_hours


def is_grid_weather_fresh(max_age_hours: float = 12) -> bool:
    latest = get_latest_grid_fetch_time()
    if latest is None:
        return False
    age_hours = _hours_since(latest)
    return age_hours is not None and age_hours <= max_age_hours


def is_port_weather_fresh(max_age_hours: float = 6) -> bool:
    latest = get_latest_port_time()
    if latest is None:
        return False
    age_hours = _hours_since(latest)
    return age_hours is not None and age_hours <= max_age_hours
