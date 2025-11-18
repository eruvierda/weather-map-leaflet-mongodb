# Weather Map – Leaflet + MongoDB

Interactive weather map for Indonesia with real-time data collection, API backend, and historical visualization.

---

## Project Structure

```
├─ backend/          # Flask API and data collectors
├─ frontend/         # LeafletJS UI and client-side caching
├─ data/             # MongoDB schema and collection info
├─ docs/             # Full documentation
├─ scripts/          # Utility/deployment scripts
└─ README.md         # This file
```

- **Backend** – API servers, collectors, and data access layer.
- **Frontend** – UI with map, charts, and smart caching.
- **Data** – MongoDB collections and schema notes.
- **Docs** – Complete setup, API, and troubleshooting guide.
- **Scripts** – Deployment and maintenance helpers.

---

## Quick Start

1. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB and API settings
   ```

3. **Collect weather data**
   ```bash
   python backend/collectors/run_all_collectors.py
   ```

4. **Start the API + UI server**
   ```bash
   python backend/api/weather_api_server_extended.py
   ```
   Visit `http://localhost:8000` to open the map.

---

## Documentation

- **Full guide**: See `docs/README.md`
- **Backend details**: See `backend/README.md`
- **Frontend guide**: See `frontend/README.md`
- **Data schema**: See `data/README.md`

---

## License

See `LICENSE` file for details.
