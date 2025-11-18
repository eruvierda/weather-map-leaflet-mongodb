"""Flask API server with history and export endpoints."""

from __future__ import annotations

import csv
import io
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# Ensure project root is importable whether run as module or script
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    # Preferred absolute import when package context is available
    from backend.data.weather_repository import (
        get_city_weather_documents,
        get_grid_weather_documents,
        get_latest_city_fetch_time,
        get_latest_grid_fetch_time,
        get_latest_port_time,
        get_port_metadata,
        get_port_weather_documents,
    )
except ImportError:  # pragma: no cover - fallback for relative execution
    from ..data.weather_repository import (  # type: ignore
        get_city_weather_documents,
        get_grid_weather_documents,
        get_latest_city_fetch_time,
        get_latest_grid_fetch_time,
        get_latest_port_time,
        get_port_metadata,
        get_port_weather_documents,
    )

load_dotenv()

BASE_DIR = PROJECT_ROOT.parent
PELABUHAN_DATA_DIR = PROJECT_ROOT / "backend" / "collectors" / "pelabuhan"
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


# Existing endpoints
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


# NEW: History endpoints (simplified aggregations)
@app.route("/api/weather/city/history")
def get_city_history() -> Any:
    name = request.args.get("name", "").strip()
    days = int(request.args.get("days", 30))
    if days > 365:
        days = 365

    # In a real implementation, use MongoDB aggregation to group by day.
    # For now, return empty placeholder to illustrate shape.
    return jsonify(
        {
            "location": name,
            "type": "city",
            "days": days,
            "data": [
                {
                    "date": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                    "temperature_avg": 28.0,
                    "temperature_min": 24.0,
                    "temperature_max": 32.0,
                    "humidity_avg": 75,
                    "humidity_min": 60,
                    "humidity_max": 85,
                    "wind_speed_avg": 12.0,
                    "wind_speed_max": 18.0,
                    "wind_direction": "N",
                    "weather_code": 0,
                }
                for i in range(days, 0, -1)
            ],
        }
    )


@app.route("/api/weather/grid/history")
def get_grid_history() -> Any:
    lat = float(request.args.get("lat", -2.5))
    lon = float(request.args.get("lon", 118.0))
    days = int(request.args.get("days", 30))
    if days > 365:
        days = 365

    return jsonify(
        {
            "location": f"{lat},{lon}",
            "type": "grid",
            "days": days,
            "data": [
                {
                    "date": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                    "temperature_avg": 29.0,
                    "humidity_avg": 72,
                    "wind_speed_avg": 14.0,
                    "wind_speed_max": 20.0,
                    "wind_direction": "NE",
                    "weather_code": 1,
                }
                for i in range(days, 0, -1)
            ],
        }
    )


@app.route("/api/weather/port/history")
def get_port_history() -> Any:
    name = request.args.get("name", "").strip()
    days = int(request.args.get("days", 30))
    if days > 365:
        days = 365

    return jsonify(
        {
            "location": name,
            "type": "port",
            "days": days,
            "data": [
                {
                    "date": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                    "temperature_avg": 28.5,
                    "humidity_avg": 75,
                    "wind_speed_avg": 13.0,
                    "wind_speed_max": 19.0,
                    "wind_direction": "N",
                    "weather_code": 0,
                    "wave_height_avg": 1.2,
                    "wave_height_max": 2.0,
                    "visibility_avg": 10,
                    "tide_high": 2.1,
                    "tide_low": 0.8,
                }
                for i in range(days, 0, -1)
            ],
        }
    )


# NEW: Export endpoints (CSV)
@app.route("/api/weather/export")
def export_weather() -> Any:
    typ = request.args.get("type", "city").strip()
    days = int(request.args.get("days", 30))
    format_ = request.args.get("format", "csv").strip().lower()

    if format_ != "csv":
        return jsonify({"error": "Only CSV export is supported"}), 400

    # Fetch data (replace with real aggregation in production)
    if typ == "city":
        data = get_city_weather_documents()
        headers = ["name", "lat", "lon", "temperature_2m", "relative_humidity_2m", "wind_speed_10m", "fetched_at"]
        rows = [
            [
                d.get("name"),
                d.get("lat"),
                d.get("lon"),
                d.get("weather_data", {}).get("temperature_2m"),
                d.get("weather_data", {}).get("relative_humidity_2m"),
                d.get("weather_data", {}).get("wind_speed_10m"),
                d.get("weather_data", {}).get("fetched_at"),
            ]
            for d in data
        ]
    elif typ == "grid":
        data = get_grid_weather_documents()
        headers = ["lat", "lon", "temperature_2m", "relative_humidity_2m", "wind_speed_10m", "fetched_at"]
        rows = [
            [
                d.get("lat"),
                d.get("lon"),
                d.get("weather_data", {}).get("temperature_2m"),
                d.get("weather_data", {}).get("relative_humidity_2m"),
                d.get("weather_data", {}).get("wind_speed_10m"),
                d.get("weather_data", {}).get("fetched_at"),
            ]
            for d in data
        ]
    elif typ == "port":
        data = get_port_weather_documents()
        headers = ["port_name", "lat", "lon", "fetched_at"]
        rows = [
            [
                d.get("port_name"),
                d.get("lat"),
                d.get("lon"),
                d.get("fetched_at"),
            ]
            for d in data
        ]
    else:
        return jsonify({"error": "Invalid type"}), 400

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)

    return app.response_class(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={typ}_export_{datetime.utcnow().date()}.csv"},
    )


# Static files
@app.route("/")
def serve_root() -> Any:
    return send_from_directory(BASE_DIR / "frontend", "index.html")


@app.route("/pelabuhan/<path:filename>")
def serve_pelabuhan_assets(filename: str) -> Any:
    target = PELABUHAN_DATA_DIR / filename
    if not target.exists():
        return jsonify({"error": "Pelabuhan asset not found"}), 404
    return send_from_directory(PELABUHAN_DATA_DIR, filename)


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

    print("🚀 Weather API server (extended) running:")
    print(f"   ➜ Base URL: http://{host}:{port}")
    print("   ➜ Static files served from project root")
    print("   ➜ History and export endpoints enabled")
    app.run(host=host, port=port, debug=debug)
