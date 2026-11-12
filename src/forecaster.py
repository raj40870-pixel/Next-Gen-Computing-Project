"""
Forecasting and Risk Assessment Engine
Generates 30-day ahead predictions, performs what-if scenario simulations (Drought, Surplus, Normal),
and classifies districts into CGWB risk categories (Safe, Semi-Critical, Critical, Over-Exploited).
"""

import os
import json
import numpy as np
import pandas as pd
import torch
from typing import Dict, Any, List, Optional, Tuple
from .models.stgnn import SpatioTemporalGNN
from .graph_builder import HydrogeologicalGraph


class GroundwaterForecaster:
    """End-to-end inference and scenario simulation engine with physically grounded scaling."""
    def __init__(
        self,
        model: SpatioTemporalGNN,
        graph: HydrogeologicalGraph,
        target_mean: float,
        target_std: float,
        feature_means: Optional[np.ndarray] = None,
        feature_stds: Optional[np.ndarray] = None,
        scaler: Optional[Dict[str, Any]] = None,
        device: str = "cpu"
    ):
        self.device = torch.device(device)
        self.model = model.to(self.device).eval()
        self.graph = graph
        self.torch_graph = graph.get_torch_graph(self.device)
        self.districts = graph.districts
        self.num_nodes = len(self.districts)

        if scaler is not None:
            self.feature_means = np.array(scaler["means"], dtype=np.float32)
            self.feature_stds = np.array(scaler["stds"], dtype=np.float32)
            self.target_mean = float(self.feature_means[0])
            self.target_std = float(self.feature_stds[0])
        else:
            self.target_mean = target_mean
            self.target_std = target_std
            self.feature_means = feature_means
            self.feature_stds = feature_stds

    def predict_next_30_days(
        self,
        last_window_norm: np.ndarray,
        rainfall_modifier: float = 1.0,
        extraction_modifier: float = 1.0
    ) -> Dict[str, Any]:
        """
        last_window_norm: [T_in, N, F] normalized input features
        rainfall_modifier: scalar e.g. 0.65 for drought, 1.4 for surplus
        extraction_modifier: scalar e.g. 1.2 for heavy pumping
        """
        inp = last_window_norm.copy()

        # Apply physically grounded scenario modification on unscaled units before re-normalizing
        if self.feature_means is not None and self.feature_stds is not None:
            if rainfall_modifier != 1.0:
                rf_m, rf_s = self.feature_means[2], self.feature_stds[2]
                rf_phys = np.clip(inp[:, :, 2] * rf_s + rf_m, a_min=0.0, a_max=None)
                rf_phys_mod = np.clip(rf_phys * rainfall_modifier, a_min=0.0, a_max=None)
                inp[:, :, 2] = (rf_phys_mod - rf_m) / (rf_s + 1e-8)

            if extraction_modifier != 1.0:
                sub_m, sub_s = self.feature_means[1], self.feature_stds[1]
                sub_phys = inp[:, :, 1] * sub_s + sub_m
                sub_phys_mod = sub_phys * extraction_modifier
                inp[:, :, 1] = (sub_phys_mod - sub_m) / (sub_s + 1e-8)

        # Expand batch dim: [1, T_in, N, F]
        x_tensor = torch.tensor(inp, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            preds_norm = self.model(x_tensor, self.torch_graph["adj"]).squeeze(0).cpu().numpy()  # [30, N]

        # Invert normalization to meters below ground level
        preds_mbgl = preds_norm * self.target_std + self.target_mean

        # Baseline start depths (last step of input window)
        current_depths_norm = last_window_norm[-1, :, 0]
        current_depths_mbgl = current_depths_norm * self.target_std + self.target_mean

        forecast_results = []
        for i in range(self.num_nodes):
            d = self.districts[i]
            cur_d = float(current_depths_mbgl[i])
            traj = preds_mbgl[:, i].tolist()
            d30_d = float(traj[-1])
            net_change = d30_d - cur_d  # positive = water table falling deeper (bad)

            # Statutory CGWB Risk Classification
            risk_category, risk_color, advisory = self._classify_risk(
                d["extraction_stage_percent"], cur_d, net_change
            )

            forecast_results.append({
                "district_id": i,
                "district_name": d["name"],
                "state": d["state"],
                "lat": d["lat"],
                "lon": d["lon"],
                "current_depth_mbgl": round(cur_d, 2),
                "forecast_day30_mbgl": round(d30_d, 2),
                "net_change_meters": round(net_change, 3),
                "trajectory_30d": [round(v, 2) for v in traj],
                "risk_category": risk_category,
                "risk_color": risk_color,
                "advisory": advisory,
                "extraction_stage_percent": d["extraction_stage_percent"]
            })

        return {
            "forecast_horizon_days": 30,
            "districts": forecast_results,
            "mean_depletion_change": round(float(np.mean([r["net_change_meters"] for r in forecast_results])), 3)
        }

    def _classify_risk(self, stage: float, depth: float, change: float) -> Tuple[str, str, str]:
        """
        Classifies district into statutory CGWB vulnerability categories:
        - Over-Exploited: Stage of Extraction > 100% or severe drawdown depth/rate
        - Critical: Stage of Extraction 90% - 100%
        - Semi-Critical: Stage of Extraction 70% - 90%
        - Safe: Stage of Extraction <= 70%
        """
        if stage > 100.0 or depth > 30.0 or change > 0.30:
            return (
                "Over-Exploited",
                "#d90429",  # Red
                "CRITICAL ALERT: Statutory CGWB Over-Exploited status (extraction exceeds 100% of annual recharge). Strictly regulate tubewell pumping and transition to micro-irrigation immediately."
            )
        elif stage >= 90.0 or depth > 22.0 or change > 0.15:
            return (
                "Critical",
                "#f77f00",  # Orange
                "WARNING: Statutory CGWB Critical category (extraction 90-100% of recharge). Implement artificial recharge structures and canal-water blending."
            )
        elif stage >= 70.0 or depth > 16.0 or change > 0.05:
            return (
                "Semi-Critical",
                "#fcbf49",  # Yellow
                "CAUTION: Statutory CGWB Semi-Critical category (extraction 70-90% of recharge). Promote crop diversification away from water-intensive paddy."
            )
        else:
            return (
                "Safe",
                "#2a9d8f",  # Green
                "STABLE: Statutory CGWB Safe category (extraction <= 70% of recharge). Aquifer levels within sustainable limits."
            )
