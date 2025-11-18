# Weather Map – Leaflet + MongoDB

Interactive weather map for Indonesia with real-time data collection, API backend, and historical visualization.

---

## Architecture Overview

- **Data Collection Layer**
  - Collectors (`backend/collectors/update_city_weather.py`, `backend/collectors/fetch_weather_data.py`, `backend/collectors/pelabuhan/pelabuhan_weather.py`) fetch weather from external APIs.
  - Orchestrator (`backend/collectors/run_all_collectors.py`) runs all collectors with retry logic and unified logging.
  - Data is stored in MongoDB collections: `city_weather`, `grid_weather`, `port_weather`.

- **Backend API Layer**
  - Flask server (`backend/api/weather_api_server.py`) serves current weather via REST.
  - Extended server (`backend/api/weather_api_server_extended.py`) adds history and CSV export endpoints.
  - Optional caching and rate limiting can be added.

- **Frontend Layer**
  - LeafletJS dashboard (`frontend/index.html`) with a smart cache manager.
  - Historical panel (Chart.js) to view trends and export CSV.
  - Responsive UI (Tailwind CSS).

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Configure environment
Copy `.env.example` to `.env` and adjust as needed:
```ini
MONGO_URI=mongodb://localhost:27017
MONGO_DB=weather_map
CITY_COLLECTION=city_weather
GRID_COLLECTION=grid_weather
PORT_COLLECTION=port_weather
WEATHER_API_HOST=0.0.0.0
WEATHER_API_PORT=8000
```

### 3. Collect weather data (one-time)
```bash
# Run all collectors with retry/orchestration
python backend/collectors/run_all_collectors.py
```

### 4. Start the API + UI server
```bash
# Standard server
python backend/api/weather_api_server.py

# OR extended server with history/export
python backend/api/weather_api_server_extended.py
```
Visit `http://localhost:8000` to open the map.

### 5. (Optional) Automate collection
- Use Windows Task Scheduler or cron to run `backend/collectors/run_all_collectors.py` every 2–3 hours.
- Logs are written to `backend/logs/collector.log`.

---

## API Endpoints

| Endpoint                              | Method | Description                              |
|---------------------------------------|--------|------------------------------------------|
| `/api/weather/city`                   | GET    | Current city weather list                |
| `/api/weather/grid`                   | GET    | Current 1° grid weather list             |
| `/api/weather/port`                   | GET    | Current port weather list                |
| `/api/weather/all`                    | GET    | Combined payload                         |
| `/api/weather/summary`                | GET    | Latest timestamps + counts               |
| `/api/weather/city/history`           | GET    | Historical aggregates for a city         |
| `/api/weather/grid/history`           | GET    | Historical aggregates for a grid point   |
| `/api/weather/port/history`           | GET    | Historical aggregates for a port         |
| `/api/weather/export`                 | GET    | CSV export (type, days, format=csv)      |

**History query examples**
```
/api/weather/city/history?name=Jakarta&days=30
/api/weather/grid/history?lat=-2.5&lon=118.0&days=90
/api/weather/port/history?name=Tanjung%20Priok&days=7
```

**Export query example**
```
/api/weather/export?type=city&days=30&format=csv
```

---

## UI Features

- **Interactive map** with city/grid/port weather layers.
- **Smart caching** via `SmartCacheManager` to reduce API calls.
- **Historical panel** (📈 button) to visualize trends for temperature, humidity, and wind speed.
- **Export** button to download current data as CSV.
- **Data freshness warnings** if underlying data is older than thresholds.

---

## Development Notes

- MongoDB is the canonical data source; static JSON files are no longer required.
- To extend history endpoints, replace placeholder generators in `backend/api/weather_api_server_extended.py` with real MongoDB aggregations.
- For production, consider:
  - Running Flask via Gunicorn/Waitress.
  - Adding API key authentication and rate limiting.
  - Using a reverse proxy (Nginx/Caddy) for SSL and static file caching.

---

## Troubleshooting

- **404s for weather data**: Ensure the API server is running and the UI is configured to call the correct base URL (see `WEATHER_API_BASE` in `frontend/index.html`).
- **Missing data**: Run collectors via `backend/collectors/run_all_collectors.py`; check `backend/logs/collector.log` for errors.
- **Historical panel empty**: Use `backend/api/weather_api_server_extended.py`; the standard server does not include history endpoints.

---

## License

See `LICENSE` file for details.
