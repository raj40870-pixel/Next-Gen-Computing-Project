"""
Baseline Models for Groundwater Depletion Forecasting
Pure PyTorch and NumPy implementations:
1. LSTMForecaster (Deep Learning temporal baseline using PyTorch)
2. RandomForestForecaster (Decision Forest Regressor implemented in pure NumPy)
3. ARIMAForecaster (AutoRegressive Integrated Moving Average model in pure NumPy)
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Any, List, Tuple, Optional


# ---------------------------------------------------------
# 1. LSTM Temporal Deep Learning Baseline (PyTorch)
# ---------------------------------------------------------
class LSTMModel(nn.Module):
    """District-level LSTM forecaster."""
    def __init__(self, input_dim: int = 4, hidden_dim: int = 48, num_layers: int = 2, seq_len_out: int = 30, dropout: float = 0.1):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, seq_len_out)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        lstm_out, _ = self.lstm(x)
        last_hidden = lstm_out[:, -1, :]
        out = self.fc(last_hidden)  # [B, T_out]
        return out


class LSTMForecaster:
    """Wrapper to train and predict across all 15 districts using LSTM."""
    def __init__(self, input_dim: int = 4, hidden_dim: int = 48, seq_len_out: int = 30, lr: float = 0.003, device: str = "cpu"):
        self.device = torch.device(device)
        self.model = LSTMModel(input_dim=input_dim, hidden_dim=hidden_dim, seq_len_out=seq_len_out).to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.criterion = nn.MSELoss()
        self.seq_len_out = seq_len_out

    def fit(self, X: np.ndarray, Y: np.ndarray, epochs: int = 15, batch_size: int = 64):
        self.model.train()
        B, T_in, N, F = X.shape
        X_flat = np.transpose(X, (0, 2, 1, 3)).reshape(-1, T_in, F)
        Y_flat = np.transpose(Y, (0, 2, 1)).reshape(-1, self.seq_len_out)

        dataset = torch.utils.data.TensorDataset(
            torch.tensor(X_flat, dtype=torch.float32),
            torch.tensor(Y_flat, dtype=torch.float32)
        )
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

        for ep in range(epochs):
            for batch_x, batch_y in loader:
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                self.optimizer.zero_grad()
                pred = self.model(batch_x)
                loss = self.criterion(pred, batch_y)
                loss.backward()
                self.optimizer.step()

    def predict(self, X: np.ndarray) -> np.ndarray:
        self.model.eval()
        B, T_in, N, F = X.shape
        X_flat = np.transpose(X, (0, 2, 1, 3)).reshape(-1, T_in, F)
        
        with torch.no_grad():
            inp = torch.tensor(X_flat, dtype=torch.float32).to(self.device)
            pred_flat = self.model(inp).cpu().numpy()
            
        pred = pred_flat.reshape(B, N, self.seq_len_out)
        return np.transpose(pred, (0, 2, 1))


# ---------------------------------------------------------
# 2. Pure NumPy Decision Tree & Random Forest Baseline
# ---------------------------------------------------------
class _Node:
    def __init__(self, feature=None, threshold=None, left=None, right=None, value=None):
        self.feature = feature
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value

    @property
    def is_leaf(self):
        return self.value is not None


class _RegressionTree:
    """Fast vectorized regression tree in pure NumPy."""
    def __init__(self, max_depth: int = 5, min_samples_split: int = 6):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.root = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.root = self._grow_tree(X, y, depth=0)

    def _grow_tree(self, X: np.ndarray, y: np.ndarray, depth: int):
        n_samples, n_features = X.shape
        if depth >= self.max_depth or n_samples < self.min_samples_split:
            return _Node(value=np.mean(y, axis=0))

        feat_idxs = np.random.choice(n_features, max(1, int(np.sqrt(n_features))), replace=False)
        best_feat, best_thresh = None, None
        best_gain = float("inf")

        for feat in feat_idxs:
            X_col = X[:, feat]
            thresholds = np.percentile(X_col, [25, 50, 75])
            for thresh in thresholds:
                left_mask = X_col <= thresh
                right_mask = ~left_mask
                if np.sum(left_mask) == 0 or np.sum(right_mask) == 0:
                    continue
                var_left = np.var(y[left_mask]) * np.sum(left_mask)
                var_right = np.var(y[right_mask]) * np.sum(right_mask)
                gain = var_left + var_right
                if gain < best_gain:
                    best_gain = gain
                    best_feat = feat
                    best_thresh = thresh

        if best_feat is None:
            return _Node(value=np.mean(y, axis=0))

        left_mask = X[:, best_feat] <= best_thresh
        left = self._grow_tree(X[left_mask], y[left_mask], depth + 1)
        right = self._grow_tree(X[~left_mask], y[~left_mask], depth + 1)
        return _Node(feature=best_feat, threshold=best_thresh, left=left, right=right)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.array([self._predict_row(x, self.root) for x in X])

    def _predict_row(self, x: np.ndarray, node: _Node):
        if node.is_leaf:
            return node.value
        if x[node.feature] <= node.threshold:
            return self._predict_row(x, node.left)
        return self._predict_row(x, node.right)


class RandomForestForecaster:
    """Random Forest regressor in pure NumPy (eliminates sklearn binary dependency)."""
    def __init__(self, n_estimators: int = 15, max_depth: int = 5, random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.forests: Dict[int, List[_RegressionTree]] = {}

    def fit(self, X: np.ndarray, Y: np.ndarray):
        """
        X: [B, T_in, N, F]
        Y: [B, T_out, N]
        """
        B, T_in, N, F = X.shape
        sub_sample = min(B, 150)
        np.random.seed(self.random_state)
        idx = np.random.choice(B, sub_sample, replace=False)

        for n in range(N):
            X_node = X[idx, :, n, :].reshape(sub_sample, -1)
            Y_node = Y[idx, :, n]
            
            trees = []
            for _ in range(self.n_estimators):
                boot_idx = np.random.choice(sub_sample, sub_sample, replace=True)
                tree = _RegressionTree(max_depth=self.max_depth)
                tree.fit(X_node[boot_idx], Y_node[boot_idx])
                trees.append(tree)
            self.forests[n] = trees

    def predict(self, X: np.ndarray) -> np.ndarray:
        B, T_in, N, F = X.shape
        # Get seq_len_out from a leaf
        T_out = len(self.forests[0][0].root.value) if hasattr(self.forests[0][0].root.value, "__len__") else 30
        preds = np.zeros((B, T_out, N), dtype=np.float32)

        for n in range(N):
            X_node = X[:, :, n, :].reshape(B, -1)
            tree_preds = np.array([tree.predict(X_node) for tree in self.forests[n]])
            preds[:, :, n] = np.mean(tree_preds, axis=0)

        return preds


# ---------------------------------------------------------
# 3. Pure NumPy ARIMA / AutoRegressive Baseline
# ---------------------------------------------------------
class ARIMAForecaster:
    """
    Pure NumPy AutoRegressive Integrated (AR(p)) Forecaster.
    Computes first-difference stationarity, solves Yule-Walker / OLS for AR coefficients,
    and extrapolates multi-step predictions.
    """
    def __init__(self, order: Optional[Tuple[int, int, int]] = None, p: int = 5, d: int = 1, seq_len_out: int = 30):
        if order is not None:
            self.p = order[0]
            self.d = order[1]
        else:
            self.p = p
            self.d = d
        self.seq_len_out = seq_len_out

    def predict(self, historical_series: np.ndarray) -> np.ndarray:
        """
        historical_series: [T_in, N] target series for each node
        returns: [T_out, N]
        """
        T_in, N = historical_series.shape
        preds = np.zeros((self.seq_len_out, N), dtype=np.float32)

        for n in range(N):
            series = historical_series[:, n]
            diff = np.diff(series) if self.d == 1 else series
            last_val = series[-1]

            # Fit AR(p) on differenced series using OLS
            if len(diff) > self.p + 2:
                X_ar = np.column_stack([diff[i : i + len(diff) - self.p] for i in range(self.p)])
                y_ar = diff[self.p :]
                # Regularized least squares
                coeffs, _, _, _ = np.linalg.lstsq(
                    X_ar.T @ X_ar + 1e-4 * np.eye(self.p),
                    X_ar.T @ y_ar,
                    rcond=None
                )
                # Multi-step autoregressive rollout
                cur_diff = list(diff[-self.p:])
                forecast_diffs = []
                for _ in range(self.seq_len_out):
                    next_diff = float(np.dot(cur_diff[-self.p:], coeffs))
                    forecast_diffs.append(next_diff)
                    cur_diff.append(next_diff)

                # Integrate back: last_val + cumsum(diffs)
                preds[:, n] = last_val + np.cumsum(forecast_diffs)
            else:
                # Linear trend fallback
                slope = (series[-1] - series[0]) / max(T_in - 1, 1)
                preds[:, n] = last_val + slope * np.arange(1, self.seq_len_out + 1)

        return preds

    def batch_predict(self, X: np.ndarray, target_idx: int = 0) -> np.ndarray:
        """
        X: [B, T_in, N, F]
        returns: [B, T_out, N]
        """
        B, T_in, N, F = X.shape
        sample_step = max(1, B // 30)
        eval_indices = list(range(0, B, sample_step))

        preds_sampled = []
        for idx in eval_indices:
            hist_node = X[idx, :, :, target_idx]
            pred = self.predict(hist_node)
            preds_sampled.append(pred)

        full_preds = np.zeros((B, self.seq_len_out, N), dtype=np.float32)
        for i, idx in enumerate(eval_indices):
            next_idx = eval_indices[i + 1] if i + 1 < len(eval_indices) else B
            for b in range(idx, next_idx):
                full_preds[b] = preds_sampled[i]

        return full_preds
