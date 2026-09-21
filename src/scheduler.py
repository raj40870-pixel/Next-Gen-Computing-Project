"""
Background Automated Satellite Synchronization Daemon
Periodically polls live satellite feeds and updates the ST-GNN forecasting model.
"""

import os
import sys
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.live_sync import LiveSatelliteSync, CONFIG_PATH


def run_scheduler_daemon(check_interval_seconds: int = 3600):
    """
    Continuous background loop that monitors sync intervals
    and triggers automated satellite data ingestion.
    """
    print("=" * 65)
    print("  AUTOMATED SATELLITE DATA SYNC DAEMON STARTED")
    print("=" * 65)

    syncer = LiveSatelliteSync()

    while True:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)

            if cfg.get("auto_sync_enabled", True):
                last_sync_str = cfg.get("last_sync_timestamp")
                interval_hours = cfg.get("sync_interval_hours", 24)

                should_sync = False
                if not last_sync_str:
                    should_sync = True
                else:
                    last_sync_dt = datetime.strptime(last_sync_str, "%Y-%m-%d %H:%M:%S")
                    hours_elapsed = (datetime.now() - last_sync_dt).total_seconds() / 3600.0
                    if hours_elapsed >= interval_hours:
                        should_sync = True

                if should_sync:
                    print(f"[{datetime.now()}] Triggering scheduled satellite synchronization...")
                    syncer.sync_all_districts()
                else:
                    print(f"[{datetime.now()}] Satellite feeds up to date. Next check in {check_interval_seconds}s.")
        except Exception as e:
            print(f"[!] Scheduler error: {e}")

        time.sleep(check_interval_seconds)


if __name__ == "__main__":
    run_scheduler_daemon(check_interval_seconds=600)
