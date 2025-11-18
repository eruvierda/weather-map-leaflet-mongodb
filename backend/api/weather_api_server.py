"""Flask API server that serves weather data from MongoDB and static assets."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from ..data.weather_repository import (
    get_city_weather_documents,
    get_grid_weather_documents,
    get_latest_city_fetch_time,
    get_latest_grid_fetch_time,
    get_latest_port_time,
    get_port_metadata,
    get_port_weather_documents,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")
CORS(app)


def _serialize(value: Any) -> Any:
    """Recursively convert datetimes to ISO strings so they are JSON serializable."""
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(val) for key, val in value.items()}
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _build_summary() -> Dict[str, Any]:
    city_latest = get_latest_city_fetch_time()
    grid_latest = get_latest_grid_fetch_time()
    port_latest = get_latest_port_time()

    return {
        "city": {
            "latest": city_latest.isoformat() if city_latest else None,
            "count": len(get_city_weather_documents()),
        },
        "grid": {
            "latest": grid_latest.isoformat() if grid_latest else None,
            "count": len(get_grid_weather_documents()),
        },
        "port": {
            "latest": port_latest.isoformat() if port_latest else None,
            "count": len(get_port_weather_documents()),
        },
    }


@app.route("/api/weather/city")
def get_city_weather() -> Any:
    data = _serialize(get_city_weather_documents())
    return jsonify(data)


@app.route("/api/weather/grid")
def get_grid_weather() -> Any:
    data = _serialize(get_grid_weather_documents())
    return jsonify(data)


@app.route("/api/weather/port")
def get_port_weather() -> Any:
    data = _serialize(get_port_weather_documents())
    return jsonify(data)


@app.route("/api/weather/port/metadata")
def get_port_metadata_endpoint() -> Any:
    data = get_port_metadata()
    return jsonify(data)


@app.route("/api/weather/all")
def get_all_weather() -> Any:
    payload: Dict[str, List[Dict[str, Any]]] = {
        "city": _serialize(get_city_weather_documents()),
        "grid": _serialize(get_grid_weather_documents()),
        "port": _serialize(get_port_weather_documents()),
    }
    return jsonify(payload)


@app.route("/api/weather/summary")
def get_weather_summary() -> Any:
    return jsonify(_build_summary())


@app.route("/")
def serve_root() -> Any:
    return send_from_directory(BASE_DIR / "frontend", "index.html")


@app.route("/<path:path>")
def serve_static(path: str) -> Any:
    target = BASE_DIR / path
    if target.is_dir():
        return send_from_directory(target, "index.html")
    return send_from_directory(BASE_DIR, path)


if __name__ == "__main__":
    host = os.getenv("WEATHER_API_HOST", "0.0.0.0")
    port = int(os.getenv("WEATHER_API_PORT", "8000"))
    debug = os.getenv("WEATHER_API_DEBUG", "false").lower() == "true"

    print("🚀 Weather API server running:")
    print(f"   ➜ Base URL: http://{host}:{port}")
    print("   ➜ Static files served from project root")
    app.run(host=host, port=port, debug=debug)
