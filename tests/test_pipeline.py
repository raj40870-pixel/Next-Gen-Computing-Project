"""
Unit and Integration Tests for Groundwater Depletion Forecasting ST-GNN
"""

import os
import sys
import json
import numpy as np
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_pipeline import load_district_metadata, generate_calibrated_timeseries, SpatioTemporalDataset
from src.graph_builder import HydrogeologicalGraph, haversine_distance
from src.models.stgnn import SpatioTemporalGNN
from src.evaluator import compute_rmse, compute_mae, compute_r2, ModelEvaluator
from src.forecaster import GroundwaterForecaster


def test_metadata_loading():
    districts = load_district_metadata()
    assert len(districts) == 23, f"Expected 23 districts of Punjab, got {len(districts)}"
    for d in districts:
        assert "name" in d
        assert "lat" in d
        assert "lon" in d
        assert "baseline_depth_m" in d
        assert "cgwb_status" in d


def test_haversine_distance():
    # Distance between Patiala (30.3398, 76.3869) and Ludhiana (30.9010, 75.8573) is ~80 km
    d = haversine_distance(30.3398, 76.3869, 30.9010, 75.8573)
    assert 60.0 < d < 100.0, f"Unexpected distance: {d}"


def test_graph_builder():
    graph = HydrogeologicalGraph()
    t_graph = graph.get_torch_graph()
    assert t_graph["num_nodes"] == 23
    assert t_graph["adj"].shape == (23, 23)
    assert t_graph["edge_index"].shape[0] == 2
    # Ensure adjacency is symmetric
    adj_np = t_graph["adj"].numpy()
    np.testing.assert_allclose(adj_np, adj_np.T, atol=1e-5)


def test_stgnn_forward_pass():
    B, T_in, N, F, T_out = 2, 30, 23, 4, 30
    x = torch.randn(B, T_in, N, F)
    adj = torch.eye(N)
    
    model = SpatioTemporalGNN(num_nodes=N, num_features=F, seq_len_in=T_in, seq_len_out=T_out)
    pred = model(x, adj)
    assert pred.shape == (B, T_out, N)
    assert not torch.isnan(pred).any()


def test_evaluation_metrics():
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([10.0, 20.0, 30.0])
    assert compute_rmse(y_true, y_pred) == 0.0
    assert compute_mae(y_true, y_pred) == 0.0
    assert np.isclose(compute_r2(y_true, y_pred), 1.0)


def test_forecaster():
    graph = HydrogeologicalGraph()
    t_graph = graph.get_torch_graph()
    N = t_graph["num_nodes"]
    model = SpatioTemporalGNN(num_nodes=N, num_features=4, seq_len_in=30, seq_len_out=30)
    
    forecaster = GroundwaterForecaster(
        model=model,
        graph=graph,
        target_mean=25.0,
        target_std=8.0
    )
    
    dummy_last_window = np.zeros((30, N, 4), dtype=np.float32)
    res = forecaster.predict_next_30_days(dummy_last_window)
    
    assert res["forecast_horizon_days"] == 30
    assert len(res["districts"]) == 23
    assert len(res["districts"][0]["trajectory_30d"]) == 30


if __name__ == "__main__":
    print("Running pipeline tests directly...")
    test_metadata_loading()
    print("[PASS] Metadata test passed")
    test_haversine_distance()
    print("[PASS] Haversine distance test passed")
    test_graph_builder()
    print("[PASS] Graph builder test passed")
    test_stgnn_forward_pass()
    print("[PASS] ST-GNN forward pass test passed")
    test_evaluation_metrics()
    print("[PASS] Evaluation metrics test passed")
    test_forecaster()
    print("[PASS] Forecaster test passed")
    print("\nALL UNIT & INTEGRATION TESTS PASSED SUCCESSFULLY! [OK]")
