"""
Model Zoo for Groundwater Depletion Forecasting
Contains ST-GNN and baseline comparative models (LSTM, ARIMA, Random Forest).
"""

from .stgnn import SpatioTemporalGNN
from .baselines import LSTMForecaster, ARIMAForecaster, RandomForestForecaster

__all__ = [
    "SpatioTemporalGNN",
    "LSTMForecaster",
    "ARIMAForecaster",
    "RandomForestForecaster"
]
