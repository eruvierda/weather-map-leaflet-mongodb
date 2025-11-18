# Backend

Flask API server and data collectors for the Weather Map project.

## Structure

- `api/` – Flask API servers
  - `weather_api_server.py` – Core API serving current weather
  - `weather_api_server_extended.py` – Adds history and CSV export endpoints
  - `serve_local.py` – Simple static file server for UI
- `collectors/` – Weather data fetchers
  - `update_city_weather.py` – City weather collector
  - `fetch_weather_data.py` – Grid weather collector
  - `pelabuhan/` – Port weather collector module
  - `run_all_collectors.py` – Orchestrator with retry and logging
- `data/` – Data access layer
  - `weather_repository.py` – MongoDB helpers
- `logs/` – Runtime logs
  - `collector.log` – Orchestrator output
- `requirements.txt` – Python dependencies

## Running

### Start API server
```bash
# Core server
python api/weather_api_server.py

# Extended server (history + export)
python api/weather_api_server_extended.py
```

### Run collectors
```bash
python collectors/run_all_collectors.py
```

### Environment
Copy `.env.example` to `.env` and configure:
- `MONGO_URI`
- `MONGO_DB`
- Collection names
- API host/port

## API Endpoints

See `../docs/README.md` for the full endpoint list.
