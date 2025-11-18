# Data

MongoDB is the canonical data store for the Weather Map project.

## Collections

- `city_weather` – City weather snapshots
- `grid_weather` – 1° grid weather snapshots
- `port_weather` – Port weather snapshots
- `city_metadata` – City reference data
- `grid_metadata` – Grid point reference data
- `port_metadata` – Port reference data

## Schema

Each weather document includes:
- Location identifiers (`name`, `lat`, `lon`)
- `weather_data` with fields like `temperature_2m`, `relative_humidity_2m`, `wind_speed_10m`
- `fetched_at` timestamp

## Indexes (recommended)

```js
// City
db.city_weather.createIndex({ "name": 1, "weather_data.fetched_at": -1 })

// Grid
db.grid_weather.createIndex({ "lat": 1, "lon": 1, "weather_data.fetched_at": -1 })

// Port
db.port_weather.createIndex({ "port_name": 1, "fetched_at": -1 })
```

## Backups/Exports

Use the `/api/weather/export` endpoint or mongodump for backups.
