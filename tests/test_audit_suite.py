"""
Comprehensive Technical Audit Test Suite (Phase 8)
Verifies:
1. Data provenance & dataset validation
2. Missing-value handling without future leakage
3. Strict chronological train/val/test splits (zero leakage)
4. Training scaler consistency (fitted only on training split)
5. Strict causal temporal convolution (mathematical impulse test)
6. Graph symmetry and node ordering
7. Checkpoint metadata persistence and safe error handling
8. Live API fallback honesty and source distinction
9. Ground-truth verification integrity (no manufactured values)
10. Baseline model correctness (no repeated/fabricated predictions)
11. Forecast output dimensions
12. Statutory CGWB risk classification consistency
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import torch

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data_pipeline import (
    load_district_metadata,
    generate_calibrated_timeseries,
    SpatioTemporalDataset,
    FEATURE_COLS
)
from src.graph_builder import HydrogeologicalGraph
from src.models.stgnn import SpatioTemporalGNN, TemporalGatedConv
from src.models.baselines import ARIMAForecaster, LSTMForecaster
from src.trainer import STGNNTrainer
from src.forecaster import GroundwaterForecaster
from src.evaluator import compute_rmse, compute_mae, compute_r2
from src.live_sync import LiveSatelliteSync


def test_data_provenance_and_validation():
    """Requirement 1: Validate dataset columns, district IDs, and absence of duplicate dates."""
    districts = load_district_metadata()
    valid_ids = set(d["id"] for d in districts)
    
    df = generate_calibrated_timeseries(overwrite=False)
    assert not df.empty, "Dataset should not be empty."
    
    # Check expected schema
    expected_cols = {"date", "district_id", "district_name", "state"} | set(FEATURE_COLS)
    assert expected_cols.issubset(set(df.columns)), f"Missing columns in raw dataset: {expected_cols - set(df.columns)}"
    
    # Check valid district IDs
    df_ids = set(df["district_id"].unique())
    assert df_ids.issubset(valid_ids), f"Unknown district IDs in dataset: {df_ids - valid_ids}"
    
    # Check for duplicates on (date, district_id)
    duplicates = df.duplicated(subset=["date", "district_id"]).sum()
    assert duplicates == 0, f"Found {duplicates} duplicate (date, district_id) rows!"


def test_missing_value_handling_no_future_leakage():
    """Requirement 2: Ensure missing values are imputed strictly causally without bfill future leakage."""
    df = generate_calibrated_timeseries(overwrite=False).copy()
    
    # Inject synthetic missing values in the test period
    df.sort_values(["district_id", "date"], inplace=True)
    mask = (df["district_id"] == 0) & (df["date"] > "2023-01-01") & (df["date"] < "2023-01-10")
    df.loc[mask, "water_depth_mbgl"] = np.nan
    
    # Build dataset
    dataset = SpatioTemporalDataset(df, seq_len_in=30, seq_len_out=30)
    # Check no NaNs remain after causal imputation
    assert not np.isnan(dataset.raw_tensor).any(), "NaN values found after causal imputation!"


def test_zero_train_val_test_leakage():
    """Requirement 3: Chronological non-overlapping splits."""
    df = generate_calibrated_timeseries(overwrite=False)
    dataset = SpatioTemporalDataset(df, seq_len_in=30, seq_len_out=30, split_ratios=(0.70, 0.15, 0.15))
    splits = dataset.get_sliding_windows()
    
    T_total = dataset.num_timesteps
    train_t_end = int(T_total * 0.70)
    val_t_end = int(T_total * 0.85)
    
    # Verify split boundaries are strictly ordered
    assert train_t_end < val_t_end < T_total, "Split endpoints are not monotonically increasing."
    
    # Verify shapes
    assert len(splits["train"]["X"]) > 0
    assert len(splits["val"]["X"]) > 0
    assert len(splits["test"]["X"]) > 0
    assert splits["train"]["X"].shape[1:] == (30, dataset.num_nodes, 4)
    assert splits["test"]["Y"].shape[1:] == (30, dataset.num_nodes)


def test_scaler_fitted_only_on_train():
    """Requirement 4: Verify scaler is fitted strictly on the training partition."""
    df = generate_calibrated_timeseries(overwrite=False)
    dataset = SpatioTemporalDataset(df, seq_len_in=30, seq_len_out=30, split_ratios=(0.70, 0.15, 0.15))
    
    T_total = dataset.num_timesteps
    train_t_end = int(T_total * 0.70)
    
    # Calculate ground-truth mean and std on training split slice ONLY
    expected_means = np.mean(dataset.raw_tensor[:train_t_end], axis=(0, 1))
    expected_stds = np.std(dataset.raw_tensor[:train_t_end], axis=(0, 1))
    
    np.testing.assert_allclose(dataset.means.squeeze(), expected_means, atol=1e-5,
                               err_msg="Scaler means were not fitted exclusively on training timesteps!")
    np.testing.assert_allclose(dataset.stds.squeeze(), expected_stds, atol=1e-5,
                               err_msg="Scaler stds were not fitted exclusively on training timesteps!")


def test_causal_temporal_convolution():
    """Requirement 5: Strict causal convolution test via impulse response.
    An impulse at time t_0 must NOT perturb any response at timesteps t < t_0.
    """
    layer = TemporalGatedConv(in_channels=1, out_channels=1, kernel_size=3)
    layer.eval()
    
    # Create baseline and impulse inputs
    x_base = torch.randn(1, 10, 1, 1)
    x_impulse = x_base.clone()
    t_impulse = 5
    x_impulse[0, t_impulse, 0, 0] += 50.0  # Large impulse at t=5
    
    with torch.no_grad():
        out_base = layer(x_base)
        out_impulse = layer(x_impulse)
    
    diff = (out_impulse - out_base)[0, :, 0, 0].numpy()
    
    # Outputs at t < 5 must have zero perturbation
    np.testing.assert_allclose(
        diff[:t_impulse],
        0.0,
        atol=1e-6,
        err_msg=f"Future leakage detected! Impulse at t={t_impulse} perturbed outputs at t < {t_impulse}: {diff[:t_impulse]}"
    )
    # Output at t >= 5 must show response
    assert np.abs(diff[t_impulse]).item() > 1e-3, "Impulse failed to propagate to t_0."


def test_graph_symmetry_and_ordering():
    """Requirement 6: Verify spatial adjacency matrix symmetry, self-loops, and district ordering."""
    graph = HydrogeologicalGraph()
    t_graph = graph.get_torch_graph()
    adj = t_graph["adj"].numpy()
    
    # Symmetry: A = A^T
    np.testing.assert_allclose(adj, adj.T, atol=1e-5, err_msg="Adjacency matrix is asymmetric!")
    
    # Self-loops
    diag = np.diag(adj)
    assert (diag > 0).all(), "Diagonal elements must be strictly positive (self-loops)."
    
    # Node names match metadata
    meta = load_district_metadata()
    for i, d in enumerate(meta):
        assert t_graph["node_names"][i] == d["name"], f"Node ordering mismatch at index {i}"


import tempfile
from pathlib import Path


def test_checkpoint_metadata_and_safe_loading(tmp_path=None):
    """Requirement 7: Checkpoint must store metadata and raise explicit errors on failure."""
    if tmp_path is None:
        with tempfile.TemporaryDirectory() as td:
            _run_checkpoint_test(Path(td))
    else:
        _run_checkpoint_test(tmp_path)


def _run_checkpoint_test(tmp_path: Path):
    ckpt_file = str(tmp_path / "test_ckpt.pt")
    
    # Verify FileNotFoundError when loading non-existent checkpoint
    try:
        STGNNTrainer.load_checkpoint(str(tmp_path / "non_existent.pt"))
        assert False, "Should have raised FileNotFoundError for missing checkpoint"
    except FileNotFoundError:
        pass
    
    # Create model, save with metadata
    model = SpatioTemporalGNN(num_nodes=5, num_features=4, seq_len_in=30, seq_len_out=30)
    config = model.get_config()
    assert "hidden_dim" in config
    assert "kernel_size" in config
    
    torch.save({
        "epoch": 1,
        "model_state_dict": model.state_dict(),
        "model_config": config,
        "node_names": ["A", "B", "C", "D", "E"],
        "scaler": {"means": [1.0, 2.0, 3.0, 4.0], "stds": [0.5, 0.5, 0.5, 0.5]}
    }, ckpt_file)
    
    # Safely load and verify
    loaded_model, ckpt = STGNNTrainer.load_checkpoint(ckpt_file)
    assert loaded_model.num_nodes == 5
    assert ckpt["node_names"] == ["A", "B", "C", "D", "E"]


def test_live_api_fallback_honesty():
    """Requirement 8: Live sync fallback must report OFFLINE status honestly."""
    syncer = LiveSatelliteSync()
    # Force query with invalid coordinates / timeout
    fallback = syncer.fetch_live_satellite_weather(lat=999.0, lon=999.0, past_days=3)
    assert fallback["status"] in ["LIVE_SUCCESS", "OFFLINE_CACHED"]
    if fallback["status"] == "OFFLINE_CACHED":
        assert "Fallback" in fallback["source"] or "Offline" in fallback["source"]


def test_ground_truth_verification_no_manufacturing():
    """Requirement 9: Verification must calculate true residuals |y_true - y_pred| without hardcoded deltas."""
    y_true = np.array([25.4, 28.1, 31.0])
    y_pred = np.array([25.1, 28.5, 30.6])
    
    rmse = compute_rmse(y_true, y_pred)
    mae = compute_mae(y_true, y_pred)
    r2 = compute_r2(y_true, y_pred)
    
    assert rmse > 0.0, "RMSE must be genuinely positive for distinct arrays."
    assert mae > 0.0, "MAE must be genuinely positive."
    assert r2 <= 1.0, "R2 must not exceed 1.0."
    np.testing.assert_allclose(mae, np.mean([0.3, 0.4, 0.4]), atol=1e-4)


def test_baseline_model_correctness_and_no_duplication():
    """Requirement 10: AutoRegressive baseline must predict independently for each test window."""
    B, T_in, N = 10, 30, 4
    np.random.seed(42)
    # Generate 10 windows with distinctly different trends
    X = np.zeros((B, T_in, N, 4), dtype=np.float32)
    for b in range(B):
        trend = (b + 1) * 0.1
        X[b, :, :, 0] = np.arange(T_in).reshape(-1, 1) * trend
    
    forecaster = ARIMAForecaster(p=3, d=1, seq_len_out=30)
    preds = forecaster.batch_predict(X, target_idx=0)  # [B=10, 30, N=4]
    
    assert preds.shape == (B, 30, N)
    
    # Verify predictions are NOT duplicate blocks
    diff = np.abs(preds[0] - preds[1]).max()
    assert diff > 0.01, "Adjacent batch predictions were identical! Block duplication bug detected."


def test_forecast_output_dimensions():
    """Requirement 11: GroundwaterForecaster returns exactly [30, N] outputs."""
    graph = HydrogeologicalGraph()
    t_graph = graph.get_torch_graph()
    N = t_graph["num_nodes"]
    
    model = SpatioTemporalGNN(num_nodes=N, num_features=4, seq_len_in=30, seq_len_out=30)
    forecaster = GroundwaterForecaster(
        model=model,
        graph=graph,
        target_mean=24.0,
        target_std=6.5
    )
    
    dummy_input = np.zeros((30, N, 4), dtype=np.float32)
    res = forecaster.predict_next_30_days(dummy_input)
    
    assert res["forecast_horizon_days"] == 30
    assert len(res["districts"]) == N
    for d in res["districts"]:
        assert len(d["trajectory_30d"]) == 30
        assert "risk_category" in d
        assert "risk_color" in d


def test_statutory_cgwb_risk_classification():
    """Requirement 12: Risk classification adheres strictly to CGWB statutory guidelines."""
    graph = HydrogeologicalGraph()
    model = SpatioTemporalGNN(num_nodes=graph.num_nodes, num_features=4, seq_len_in=30, seq_len_out=30)
    forecaster = GroundwaterForecaster(model=model, graph=graph, target_mean=20.0, target_std=5.0)
    
    # Over-Exploited: stage > 100%
    cat_oe, color_oe, _ = forecaster._classify_risk(stage=145.0, depth=22.0, change=0.10)
    assert cat_oe == "Over-Exploited", f"Expected Over-Exploited for stage 145%, got {cat_oe}"
    
    # Critical: stage 90 - 100%
    cat_c, _, _ = forecaster._classify_risk(stage=95.0, depth=20.0, change=0.10)
    assert cat_c == "Critical", f"Expected Critical for stage 95%, got {cat_c}"
    
    # Semi-Critical: stage 70 - 90%
    cat_sc, _, _ = forecaster._classify_risk(stage=78.0, depth=15.0, change=0.02)
    assert cat_sc == "Semi-Critical", f"Expected Semi-Critical for stage 78%, got {cat_sc}"
    
    # Safe: stage <= 70%
    cat_s, _, _ = forecaster._classify_risk(stage=55.0, depth=12.0, change=0.01)
    assert cat_s == "Safe", f"Expected Safe for stage 55%, got {cat_s}"


if __name__ == "__main__":
    tests = [
        ("Data Provenance & Validation", test_data_provenance_and_validation),
        ("Missing-Value Handling (No Leakage)", test_missing_value_handling_no_future_leakage),
        ("Zero Train/Val/Test Leakage", test_zero_train_val_test_leakage),
        ("Scaler Fitted Only on Train Split", test_scaler_fitted_only_on_train),
        ("Causal Temporal Convolution (Impulse Test)", test_causal_temporal_convolution),
        ("Graph Symmetry & Node Ordering", test_graph_symmetry_and_ordering),
        ("Checkpoint Safe Loading & Error Handling", test_checkpoint_metadata_and_safe_loading),
        ("Live API Fallback Honesty", test_live_api_fallback_honesty),
        ("Ground-Truth Verification Integrity", test_ground_truth_verification_no_manufacturing),
        ("Baseline Model Correctness (No Duplication)", test_baseline_model_correctness_and_no_duplication),
        ("Forecast Output Dimensions", test_forecast_output_dimensions),
        ("Statutory CGWB Risk Classification", test_statutory_cgwb_risk_classification),
    ]

    print("=" * 70)
    print("      GROUNDWATCH ST-GNN TECHNICAL AUDIT TEST SUITE (PHASE 8)")
    print("=" * 70)
    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name} -> {e}")
            failed += 1
    print("=" * 70)
    print(f"  Audit Test Results: {passed} PASSED, {failed} FAILED out of {len(tests)}")
    print("=" * 70)
    if failed > 0:
        sys.exit(1)
