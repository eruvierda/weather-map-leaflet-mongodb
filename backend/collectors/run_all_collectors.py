#!/usr/bin/env python3
"""
Orchestrator to run all weather data collectors with retry logic and unified logging.
"""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, List

# Configure unified logging
LOG_FILE = Path(__file__).parent.parent / "logs" / "collector.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("orchestrator")

# Collectors to run
COLLECTORS = [
    {"module": "update_city_weather", "function": "main", "name": "City Weather"},
    {"module": "fetch_weather_data", "function": "main", "name": "Grid Weather"},
    {"module": "pelabuhan.pelabuhan_weather", "function": "main", "name": "Port Weather"},
]

MAX_RETRIES = 3
BASE_DELAY_SECONDS = 5


def run_with_retry(func: Callable, name: str) -> bool:
    """Run a collector function with exponential backoff retry."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info(f"[{name}] Attempt {attempt}/{MAX_RETRIES}")
            func()
            log.info(f"[{name}] ✅ Success on attempt {attempt}")
            return True
        except Exception as e:
            log.warning(f"[{name}] ❌ Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                delay = BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                log.info(f"[{name}] Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                log.error(f"[{name}] All {MAX_RETRIES} attempts failed.")
    return False


def import_collector(module_name: str, function_name: str) -> Callable:
    """Dynamically import a collector function."""
    try:
        module = __import__(module_name, fromlist=[function_name])
        return getattr(module, function_name)
    except Exception as e:
        log.error(f"Failed to import {module_name}.{function_name}: {e}")
        raise


def main() -> None:
    start = datetime.utcnow()
    log.info("=" * 60)
    log.info("🚀 Weather Data Collection Orchestrator started")
    log.info(f"Started at: {start.isoformat()}")

    results = []
    for collector in COLLECTORS:
        name = collector["name"]
        module = collector["module"]
        func_name = collector["function"]
        log.info(f"--- Running {name} ---")
        try:
            func = import_collector(module, func_name)
            success = run_with_retry(func, name)
            results.append({"name": name, "success": success})
        except Exception as e:
            log.error(f"Failed to load {name}: {e}")
            results.append({"name": name, "success": False, "error": str(e)})

    # Summary
    log.info("--- Summary ---")
    for r in results:
        status = "✅ Success" if r["success"] else "❌ Failed"
        log.info(f"{r['name']}: {status}")
        if not r["success"] and "error" in r:
            log.info(f"  Error: {r['error']}")

    duration = datetime.utcnow() - start
    log.info(f"Orchestrator finished in {duration.total_seconds():.1f} seconds")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
