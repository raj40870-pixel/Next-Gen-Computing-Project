"""
Master Pipeline CLI Runner
Runs end-to-end data fusion, graph construction, ST-GNN training,
baseline benchmarking (LSTM, ARIMA, Random Forest), and 30-day forecasting.
"""

import os
import sys

# Prevent AppLocker DLL block on pyarrow._compute in Windows environment
sys.modules['pyarrow'] = None
sys.modules['pyarrow.compute'] = None

import json
import numpy as np
import pandas as pd
import torch

from src.data_pipeline import generate_calibrated_timeseries, SpatioTemporalDataset
from src.graph_builder import HydrogeologicalGraph
from src.models.stgnn import SpatioTemporalGNN
from src.models.baselines import LSTMForecaster, RandomForestForecaster, ARIMAForecaster
from src.trainer import STGNNTrainer
from src.evaluator import ModelEvaluator
from src.forecaster import GroundwaterForecaster


def run_full_pipeline():
    print("=" * 70)
    print("  GROUNDWATER DEPLETION FORECASTING PIPELINE (ST-GNN)")
    print("  Fusing Sentinel-1 InSAR Subsidence & IMD/CHIRPS Rainfall Data")
    print("=" * 70)

    # 1. Check Device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Execution device: {device.upper()}")

    # 2. Data Preparation
    print("\n[Step 1/6] Ingesting and aligning multi-source satellite & hydrogeological data...")
    raw_df = generate_calibrated_timeseries()
    dataset = SpatioTemporalDataset(raw_df, seq_len_in=30, seq_len_out=30)
    splits = dataset.get_sliding_windows()
    meta = splits["meta"]
    print(f"[+] Dataset created: {dataset.num_nodes} district nodes, {dataset.num_timesteps} daily steps.")
    print(f"[+] Input window: {meta['seq_len_in']} days -> Forecast horizon: {meta['seq_len_out']} days.")
    print(f"[+] Samples: Train={len(splits['train']['X'])}, Val={len(splits['val']['X'])}, Test={len(splits['test']['X'])}")

    # 3. Spatial Aquifer Graph Construction
    print("\n[Step 2/6] Constructing hydrogeological spatial graph and distance adjacency...")
    graph = HydrogeologicalGraph()
    t_graph = graph.get_torch_graph()
    district_names = t_graph["node_names"]
    print(f"[+] Constructed graph with {t_graph['num_nodes']} nodes and {t_graph['edge_index'].shape[1]} hydrogeological edges.")
    print(f"[+] Average connectivity degree: {t_graph['adj'].sum().item() / t_graph['num_nodes']:.2f}")

    # 4. ST-GNN Model Training
    print("\n[Step 3/6] Training Spatio-Temporal Graph Neural Network (ST-GNN)...")
    stgnn_model = SpatioTemporalGNN(
        num_nodes=meta["num_nodes"],
        num_features=meta["num_features"],
        seq_len_in=meta["seq_len_in"],
        seq_len_out=meta["seq_len_out"],
        hidden_dim=64,
        num_blocks=2,
        dropout=0.15
    )
    trainer = STGNNTrainer(
        model=stgnn_model,
        adj_matrix=t_graph["adj"],
        lr=0.003,
        weight_decay=1e-4,
        device=device,
        checkpoint_dir="checkpoints"
    )
    ckpt_path = os.path.join("checkpoints", "best_stgnn.pt")
    loaded = False
    if os.path.exists(ckpt_path):
        try:
            ckpt = torch.load(ckpt_path, map_location=device)
            stgnn_model.load_state_dict(ckpt["model_state_dict"])
            print(f"[+] Found compatible trained checkpoint at {ckpt_path}. Loaded weights.")
            loaded = True
        except Exception:
            print("[*] Graph structure updated (now all 23 Punjab districts). Retraining ST-GNN...")

    if not loaded:
        history = trainer.fit(
            train_data=splits["train"],
            val_data=splits["val"],
            epochs=15,
            batch_size=32,
            patience=4,
            verbose=True
        )

    # 5. Baseline Models Training & Inference
    print("\n[Step 4/6] Training baseline models (LSTM, Random Forest, ARIMA)...")
    
    # LSTM
    print("  -> Training LSTM Baseline...")
    lstm = LSTMForecaster(input_dim=meta["num_features"], hidden_dim=48, seq_len_out=meta["seq_len_out"], device=device)
    lstm.fit(splits["train"]["X"], splits["train"]["Y"], epochs=12, batch_size=64)
    lstm_preds = lstm.predict(splits["test"]["X"])

    # Random Forest
    print("  -> Training Random Forest Regressor Baseline...")
    rf = RandomForestForecaster(n_estimators=40, max_depth=10)
    rf.fit(splits["train"]["X"], splits["train"]["Y"])
    rf_preds = rf.predict(splits["test"]["X"])

    # ARIMA
    print("  -> Generating ARIMA Predictions...")
    arima = ARIMAForecaster(order=(1, 1, 1), seq_len_out=meta["seq_len_out"])
    arima_preds = arima.batch_predict(splits["test"]["X"], target_idx=meta["target_idx"])

    # ST-GNN Predictions
    stgnn_preds = trainer.predict(splits["test"]["X"])

    # 6. Evaluation & Benchmarking
    print("\n[Step 5/6] Benchmarking model performance against ground truth on test split...")
    evaluator = ModelEvaluator(
        target_mean=meta["target_mean"],
        target_std=meta["target_std"],
        district_names=district_names
    )

    y_test_norm = splits["test"]["Y"]
    res_stgnn = evaluator.evaluate_model(y_test_norm, stgnn_preds, model_name="Proposed ST-GNN")
    res_lstm = evaluator.evaluate_model(y_test_norm, lstm_preds, model_name="LSTM Baseline")
    res_rf = evaluator.evaluate_model(y_test_norm, rf_preds, model_name="Random Forest Baseline")
    res_arima = evaluator.evaluate_model(y_test_norm, arima_preds, model_name="ARIMA Baseline")

    all_results = {
        "ST-GNN": res_stgnn,
        "LSTM": res_lstm,
        "Random Forest": res_rf,
        "ARIMA": res_arima
    }

    # Print summary comparison table
    print("\n" + "=" * 70)
    print("               MODEL BENCHMARKING SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Model Architecture':<25} | {'RMSE (m)':<10} | {'MAE (m)':<10} | {'R² Score':<10}")
    print("-" * 70)
    for m_name, r in all_results.items():
        print(f"{m_name:<25} | {r['overall']['rmse']:<10.3f} | {r['overall']['mae']:<10.3f} | {r['overall']['r2']:<10.3f}")
    print("=" * 70)

    # Save benchmark results
    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print("[+] Benchmark results exported to data/processed/benchmark_results.json")

    # 7. 30-Day Forward Forecast & Scenario Analysis
    print("\n[Step 6/6] Generating 30-Day Operational Depletion Forecast...")
    forecaster = GroundwaterForecaster(
        model=stgnn_model,
        graph=graph,
        target_mean=meta["target_mean"],
        target_std=meta["target_std"],
        device=device
    )

    # Predict using the latest available window in dataset
    last_window = dataset.norm_tensor[-meta["seq_len_in"]:]
    forecast_30d = forecaster.predict_next_30_days(last_window)

    with open("data/processed/latest_forecast.json", "w", encoding="utf-8") as f:
        json.dump(forecast_30d, f, indent=2)
    print(f"[+] 30-day forecast generated for all {len(forecast_30d['districts'])} districts.")
    print(f"[+] Average predicted water table change: {forecast_30d['mean_depletion_change']:+.3f} meters.")

    print("\n" + "=" * 70)
    print("  PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("  Ready to launch the Interactive Streamlit Web Dashboard: streamlit run app.py")
    print("=" * 70)


if __name__ == "__main__":
    run_full_pipeline()
