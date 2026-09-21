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
from typing import Dict, Any, List, Tuple
from .models.stgnn import SpatioTemporalGNN
from .graph_builder import HydrogeologicalGraph


class GroundwaterForecaster:
    """End-to-end inference and scenario simulation engine."""
    def __init__(
        self,
        model: SpatioTemporalGNN,
        graph: HydrogeologicalGraph,
        target_mean: float,
        target_std: float,
        device: str = "cpu"
    ):
        self.device = torch.device(device)
        self.model = model.to(self.device).eval()
        self.graph = graph
        self.torch_graph = graph.get_torch_graph(self.device)
        self.target_mean = target_mean
        self.target_std = target_std
        self.districts = graph.districts
        self.num_nodes = len(self.districts)

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
        # Apply scenario modification to features if simulated
        inp = last_window_norm.copy()
        # feature index 2 is rainfall_mm, 1 is insar_subsidence_mm
        inp[:, :, 2] *= rainfall_modifier
        inp[:, :, 1] *= extraction_modifier

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

            # CGWB Risk Classification
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
        """Classifies district into CGWB vulnerability categories."""
        if stage > 200 or depth > 35.0 or change > 0.35:
            return (
                "Over-Exploited",
                "#d90429",  # Red
                "CRITICAL ALERT: Severe aquifer drawdown detected. Strictly regulate tubewell pumping and transition to micro-irrigation immediately."
            )
        elif stage >= 100 or depth > 25.0 or change > 0.15:
            return (
                "Critical",
                "#f77f00",  # Orange
                "WARNING: Water extraction exceeds recharge capacity. Implement artificial recharge structures and canal-water blending."
            )
        elif stage >= 70 or depth > 18.0:
            return (
                "Semi-Critical",
                "#fcbf49",  # Yellow
                "CAUTION: Water table approaching stress threshold. Promote crop diversification away from water-intensive paddy."
            )
        else:
            return (
                "Safe",
                "#2a9d8f",  # Green
                "STABLE: Aquifer levels within sustainable limits. Maintain regular monitoring."
            )
