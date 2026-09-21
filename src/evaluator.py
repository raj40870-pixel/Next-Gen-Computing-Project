"""
Model Evaluator and Benchmarking Module
Computes RMSE, MAE, and R² metrics overall and per district.
Formulates benchmarking tables comparing ST-GNN against LSTM, ARIMA, and Random Forest.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root Mean Squared Error."""
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error."""
    return float(np.mean(np.abs(y_true - y_pred)))


def compute_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Coefficient of Determination (R² Score)."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2) + 1e-8
    return float(1.0 - (ss_res / ss_tot))


class ModelEvaluator:
    """Evaluates multi-step forecasts and generates benchmarking tables."""
    def __init__(self, target_mean: float = 0.0, target_std: float = 1.0, district_names: List[str] = None):
        self.target_mean = target_mean
        self.target_std = target_std
        self.district_names = district_names or [f"District_{i}" for i in range(15)]

    def inverse_transform(self, y_norm: np.ndarray) -> np.ndarray:
        """Converts normalized predictions back to actual meters below ground level (mbgl)."""
        return y_norm * self.target_std + self.target_mean

    def evaluate_model(
        self,
        y_true_norm: np.ndarray,
        y_pred_norm: np.ndarray,
        model_name: str = "Model"
    ) -> Dict[str, Any]:
        """
        y_true_norm: [B, T_out, N]
        y_pred_norm: [B, T_out, N]
        """
        y_true = self.inverse_transform(y_true_norm)
        y_pred = self.inverse_transform(y_pred_norm)

        # Global metrics
        overall_rmse = compute_rmse(y_true, y_pred)
        overall_mae = compute_mae(y_true, y_pred)
        overall_r2 = compute_r2(y_true, y_pred)

        # District-wise breakdown
        N = y_true.shape[2]
        per_district = []
        for i in range(N):
            d_name = self.district_names[i] if i < len(self.district_names) else f"D_{i}"
            yt = y_true[:, :, i]
            yp = y_pred[:, :, i]
            per_district.append({
                "district_id": i,
                "district_name": d_name,
                "rmse": compute_rmse(yt, yp),
                "mae": compute_mae(yt, yp),
                "r2": compute_r2(yt, yp)
            })

        return {
            "model_name": model_name,
            "overall": {
                "rmse": overall_rmse,
                "mae": overall_mae,
                "r2": overall_r2
            },
            "per_district": per_district
        }

    def generate_benchmark_summary(self, results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """
        Formats comparative results into a clean presentation dataframe.
        """
        rows = []
        for model_name, res in results.items():
            overall = res["overall"]
            rows.append({
                "Model": model_name,
                "RMSE (meters)": f"{overall['rmse']:.3f}",
                "MAE (meters)": f"{overall['mae']:.3f}",
                "R² Score": f"{overall['r2']:.3f}",
                "Improvement over Baseline (%)": "—"
            })

        df = pd.DataFrame(rows)
        # Calculate percentage improvement of ST-GNN relative to worst baseline if available
        return df
