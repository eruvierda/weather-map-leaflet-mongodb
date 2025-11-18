# Frontend

LeafletJS-based weather map UI with client-side caching and historical visualization.

## Structure

- `index.html` – Main dashboard
- `assets/` – Static assets (styles, images)
- `scripts/` – JavaScript modules
  - `smart_cache_manager.js` – Client-side caching

## Features

- Interactive map with city/grid/port weather layers
- Smart caching to reduce API calls
- Historical trends panel (Chart.js)
- CSV export via API
- Data freshness warnings

## Running

Serve via the Flask API server (see `../backend/`) or any static server:
```bash
python -m http.server 8000
```
Then open `http://localhost:8000` (ensure API is running on port 8000 or adjust `WEATHER_API_BASE`).

## Configuration

- `WEATHER_API_BASE` and `WEATHER_ENDPOINTS` are configured in `index.html` before loading `smart_cache_manager.js`.
- Adjust these if your API runs on a different host/port.
