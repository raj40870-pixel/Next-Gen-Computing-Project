"""
Real-Time Environmental Data Ingestion and Live Forecasting Engine
Connects to the Open-Meteo API for real-time weather and evapotranspiration data.
Integrates observations into the calibrated spatio-temporal pipeline and triggers ST-GNN predictions.

Scientific Provenance & Status:
- Open-Meteo API: Live real-time observation (precipitation, reference ET0, temperature)
- Sentinel-1 InSAR Deformation: Calibrated PS-InSAR literature baseline (Demonstration-Only;
  real-time automated InSAR requires heavy SAR phase interferometry processing pipelines)
- CGWB Piezometer Telemetry: Benchmark reference baseline (Live API unavailable without India-WRIS credentials)
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
import numpy as np
import pandas as pd
import torch

from src.models.stgnn import SpatioTemporalGNN
from src.graph_builder import HydrogeologicalGraph
from src.forecaster import GroundwaterForecaster
from src.trainer import STGNNTrainer

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "api_config.json")
GEO_PATH = os.path.join(BASE_DIR, "data", "geo", "punjab_haryana_districts.json")
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "fused_groundwater_timeseries_2017_2024.csv")
SCALER_PATH = os.path.join(BASE_DIR, "data", "processed", "scaler.json")
FORECAST_PATH = os.path.join(BASE_DIR, "data", "processed", "latest_forecast.json")
SYNC_STATUS_PATH = os.path.join(BASE_DIR, "data", "processed", "sync_status.json")
CHECKPOINT_PATH = os.path.join(BASE_DIR, "checkpoints", "best_stgnn.pt")


class LiveSatelliteSync:
    """Manages real-time environmental data polling and honest model execution."""
    def __init__(self, config_path: str = CONFIG_PATH):
        self.config_path = config_path
        self.config = self._load_config()
        self.districts = self._load_districts()

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "auto_sync_enabled": True,
            "sync_interval_hours": 24,
            "open_meteo": {"enabled": True},
            "sentinel1_cdse": {"enabled": False, "status": "Demonstration (Requires SAR Interferometry Engine)"},
            "cgwb_telemetry": {"enabled": False, "status": "Demonstration (Requires India-WRIS credentials)"}
        }

    def _save_config(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def _load_districts(self) -> List[Dict[str, Any]]:
        with open(GEO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def fetch_live_satellite_weather(self, lat: float, lon: float, past_days: int = 7) -> Dict[str, Any]:
        """
        Queries Open-Meteo real-time weather API for observed precipitation and reference ET0.
        Variables received: precipitation_sum (mm), et0_fao_evapotranspiration (mm), temperature_2m_mean (C).
        """
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ["precipitation_sum", "et0_fao_evapotranspiration", "temperature_2m_mean"],
            "past_days": past_days,
            "forecast_days": 1,
            "timezone": "Asia/Kolkata"
        }
        try:
            resp = requests.get(url, params=params, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                daily = data.get("daily", {})
                dates = daily.get("time", [])
                precip = daily.get("precipitation_sum", [])
                et = daily.get("et0_fao_evapotranspiration", [])
                temp = daily.get("temperature_2m_mean", [])
                return {
                    "status": "LIVE_SUCCESS",
                    "source": "Open-Meteo API (Live Telemetry)",
                    "dates": dates,
                    "rainfall_mm": [float(p) if p is not None else 0.0 for p in precip],
                    "et_mm": [float(e) if e is not None else 3.5 for e in et],
                    "temp_c": [float(t) if t is not None else 28.0 for t in temp]
                }
        except Exception as e:
            pass

        # Honest fallback when internet is unavailable: mark status as cached/simulated
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(past_days, -1, -1)]
        return {
            "status": "OFFLINE_CACHED",
            "source": "Local Calibrated Seasonal Baseline (Offline Fallback)",
            "dates": dates,
            "rainfall_mm": [0.0 for _ in dates],
            "et_mm": [3.2 for _ in dates],
            "temp_c": [28.5 for _ in dates]
        }

    def sync_all_districts(self) -> Dict[str, Any]:
        """
        Fetches live weather telemetry for all 15 districts in parallel,
        records observations, and executes live ST-GNN inference.
        """
        from concurrent.futures import ThreadPoolExecutor
        print(f"[*] Ingesting environmental telemetry across {len(self.districts)} districts...")
        sync_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def _fetch_node_telemetry(d):
            d_id = d["id"]
            d_name = d["name"]
            lat = d["lat"]
            lon = d["lon"]

            weather_data = self.fetch_live_satellite_weather(lat, lon, past_days=5)
            recent_rain = weather_data["rainfall_mm"][-1] if weather_data["rainfall_mm"] else 0.0
            recent_et = weather_data["et_mm"][-1] if weather_data["et_mm"] else 3.5

            # Calibrated baseline subsidence rate
            daily_subsidence_delta = (d.get("mean_subsidence_mm_yr", -15.0) / 365.25)
            adjusted_subsidence_delta = daily_subsidence_delta + 0.05 * recent_rain

            return {
                "district_id": d_id,
                "district_name": d_name,
                "state": d["state"],
                "lat": lat,
                "lon": lon,
                "weather_api_status": weather_data["status"],
                "weather_source": weather_data["source"],
                "live_rainfall_mm": round(recent_rain, 2),
                "live_et_mm": round(recent_et, 2),
                "insar_source": "Calibrated PS-InSAR Literature Baseline (Demonstration)",
                "live_insar_delta_mm": round(adjusted_subsidence_delta, 3),
                "cgwb_source": "CGWB Historical Monitoring Well Baseline (Demonstration)",
                "last_observation_date": weather_data["dates"][-1] if weather_data["dates"] else sync_timestamp
            }

        with ThreadPoolExecutor(max_workers=15) as executor:
            telemetry_records = list(executor.map(_fetch_node_telemetry, self.districts))

        total_precip_collected = sum(r["live_rainfall_mm"] for r in telemetry_records)
        live_count = sum(1 for r in telemetry_records if r["weather_api_status"] == "LIVE_SUCCESS")

        # Run Live ST-GNN Model Inference
        print("[*] Running live ST-GNN forward pass on updated telemetry...")
        prediction_results = self._run_live_inference(telemetry_records)

        # Save Sync Status
        sync_summary = {
            "last_sync_timestamp": sync_timestamp,
            "sync_status": "SUCCESS" if live_count > 0 else "OFFLINE_FALLBACK",
            "active_nodes_synced": len(self.districts),
            "live_weather_nodes": live_count,
            "total_rainfall_monitored_mm": round(total_precip_collected, 2),
            "telemetry": telemetry_records,
            "prediction_summary": prediction_results
        }

        os.makedirs(os.path.dirname(SYNC_STATUS_PATH), exist_ok=True)
        with open(SYNC_STATUS_PATH, "w", encoding="utf-8") as f:
            json.dump(sync_summary, f, indent=2)

        # Update config metadata
        self.config["last_sync_timestamp"] = sync_timestamp
        self.config["records_synced_count"] = self.config.get("records_synced_count", 0) + len(telemetry_records)
        self._save_config()

        print(f"[+] Environmental synchronization completed at {sync_timestamp} ({live_count}/{len(self.districts)} live nodes).")
        return sync_summary

    def _run_live_inference(self, telemetry_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        graph = HydrogeologicalGraph()
        num_nodes = len(self.districts)

        # Load scaler metadata
        scaler = None
        if os.path.exists(SCALER_PATH):
            with open(SCALER_PATH, "r", encoding="utf-8") as f:
                scaler = json.load(f)
            means = np.array(scaler["means"], dtype=np.float32)
            stds = np.array(scaler["stds"], dtype=np.float32)
        else:
            means = np.array([24.0, -18.0, 2.5, 3.5], dtype=np.float32)
            stds = np.array([6.5, 7.0, 4.0, 1.2], dtype=np.float32)

        # Load trained ST-GNN model with strict validation
        if not os.path.exists(CHECKPOINT_PATH):
            raise FileNotFoundError(f"Model checkpoint not found at {CHECKPOINT_PATH}. Run training pipeline first.")

        model, ckpt = STGNNTrainer.load_checkpoint(CHECKPOINT_PATH, device="cpu")

        # Load latest historical data slice
        if os.path.exists(RAW_DATA_PATH):
            df_hist = pd.read_csv(RAW_DATA_PATH, parse_dates=["date"])
            max_dt = df_hist["date"].max()
            df_hist = df_hist[df_hist["date"] >= (max_dt - pd.Timedelta(days=45))]
        else:
            from src.data_pipeline import generate_calibrated_timeseries
            df_hist = generate_calibrated_timeseries()

        # Extract last 30 days of data across all 15 nodes
        feature_cols = ["water_depth_mbgl", "insar_subsidence_mm", "rainfall_mm", "evapotranspiration_mm"]
        pivots = []
        for feat in feature_cols:
            p = df_hist.pivot(index="date", columns="district_id", values=feat).sort_index().ffill().bfill()
            pivots.append(p.values[-30:])  # shape: [30, 15]

        # Stack into [30, 15, 4]
        tensor_30d = np.stack(pivots, axis=-1).astype(np.float32)

        # Correctly normalize using the training scaler
        norm_tensor = (tensor_30d - means.reshape(1, 1, -1)) / (stds.reshape(1, 1, -1) + 1e-8)

        # Integrate the latest real-time telemetry into the last timestep using proper scaling
        for rec in telemetry_records:
            nid = rec["district_id"]
            # Scale physical mm to z-score before insertion
            norm_tensor[-1, nid, 2] = (rec["live_rainfall_mm"] - means[2]) / (stds[2] + 1e-8)
            norm_tensor[-1, nid, 3] = (rec["live_et_mm"] - means[3]) / (stds[3] + 1e-8)

        forecaster = GroundwaterForecaster(
            model=model,
            graph=graph,
            target_mean=float(means[0]),
            target_std=float(stds[0]),
            scaler=scaler,
            device="cpu"
        )

        latest_fc = forecaster.predict_next_30_days(norm_tensor)

        # Persist updated forecast
        os.makedirs(os.path.dirname(FORECAST_PATH), exist_ok=True)
        with open(FORECAST_PATH, "w", encoding="utf-8") as f:
            json.dump(latest_fc, f, indent=2)

        return {
            "forecast_horizon_days": 30,
            "mean_depletion_change_m": latest_fc["mean_depletion_change"],
            "districts_predicted_count": len(latest_fc["districts"]),
            "critical_districts": [
                d["district_name"] for d in latest_fc["districts"] if d["risk_category"] in ["Critical", "Over-Exploited"]
            ]
        }

    def check_and_auto_sync(self, max_age_hours: float = 24.0) -> bool:
        """
        Autonomous check: executes sync if last sync is older than max_age_hours.
        """
        last_t_str = self.config.get("last_sync_timestamp")
        needs_sync = False
        if not last_t_str:
            needs_sync = True
        else:
            try:
                last_dt = datetime.strptime(last_t_str, "%Y-%m-%d %H:%M:%S")
                if (datetime.now() - last_dt).total_seconds() >= max_age_hours * 3600:
                    needs_sync = True
            except Exception:
                needs_sync = True

        if needs_sync:
            print(f"[!] Triggering sync: Last sync ({last_t_str}) is older than {max_age_hours}h.")
            self.sync_all_districts()
            return True
        return False


_BACKGROUND_DAEMON_STARTED = False

def start_autonomous_background_daemon(sync_interval_hours: float = 24.0, check_loop_seconds: int = 1800):
    """
    Spawns background sync daemon thread.
    """
    global _BACKGROUND_DAEMON_STARTED
    if _BACKGROUND_DAEMON_STARTED:
        return
    import threading

    def _daemon_worker():
        syncer = LiveSatelliteSync()
        while True:
            try:
                syncer.check_and_auto_sync(max_age_hours=sync_interval_hours)
            except Exception as e:
                print(f"[!] Background sync daemon warning: {e}")
            time.sleep(check_loop_seconds)

    t = threading.Thread(target=_daemon_worker, daemon=True, name="Groundwater-Autonomous-Daemon")
    t.start()
    _BACKGROUND_DAEMON_STARTED = True
    print("[+] Environmental Background Synchronization Daemon initialized successfully.")


if __name__ == "__main__":
    syncer = LiveSatelliteSync()
    res = syncer.sync_all_districts()
    print("Sync Status:", res["sync_status"])
    print("Last Timestamp:", res["last_sync_timestamp"])
    print("Critical Districts:", res["prediction_summary"]["critical_districts"])
