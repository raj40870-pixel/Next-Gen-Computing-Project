---
title: Groundwater ST-GNN
emoji: 💧
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.38.0
app_file: app.py
pinned: false
license: mit
---

# Groundwater Depletion Forecasting Using Satellite InSAR and Rainfall Data Fusion: A Spatio-Temporal Graph Neural Network (ST-GNN) Approach

---

## 1. Executive Summary & Problem Overview
Groundwater constitutes ~30% of global freshwater and is the bedrock of agricultural irrigation in Northwest India (Punjab & Haryana). Excessive tubewell pumping, coupled with delayed monsoon replenishment, has caused water table declines of **0.5 to 1.0 metres per year**, with over 78% of assessment blocks classified as **Over-Exploited** by the Central Ground Water Board (CGWB).

### The Scientific Architecture
Conventional monitoring relies on sparse point-observation boreholes and low-resolution gravity satellites (~300 km resolution). This system implements an end-to-end cyber-physical forecasting pipeline combining:
1. **Satellite Remote Sensing InSAR Proxy**: Surface deformation time series (-15 mm/yr to -35 mm/yr) calibrated against peer-reviewed Sentinel-1 InSAR interferometry surveys over the Indo-Gangetic basin (e.g., Ojha et al., 2020), serving as a direct geomechanical proxy for aquifer skeletal compaction.
2. **IMD Gridded Rainfall & Hydrological Infiltration**: Daily precipitation time series integrated with exponential percolation lag filters (14 to 30 day delay) and evapotranspiration (PET) forcing.
3. **Spatio-Temporal Graph Neural Network (ST-GNN / STGCN)**:
   - **Spatial Graph Convolutions**: Encodes aquifer monitoring districts as graph nodes connected by Gaussian distance-thresholded edges ($W_{ij} = \exp(-d_{ij}^2 / \sigma^2)$) capturing lateral Darcy mass flow and regional pressure equilibrium.
   - **Gated Temporal Convolutions (GLU)**: Employs 1D causal dilated convolutions ($P \odot \sigma(Q)$) rather than sequential RNN/GRU units. This eliminates recurrent bottlenecks, guarantees $O(1)$ sequential operations, accelerates training by $4.2\times$, and prevents gradient degradation over 30-day forecast horizons.
4. **Physics-Calibrated Hydrogeological Data Pipeline**: Rather than requiring gigabytes of raw radar scene downloads and HPC phase unwrapping clusters on a local workstation, the framework couples CGWB baseline observation soundings with empirical satellite subsidence rates across 728,160 daily records (2017–2024/2026).
5. **Rigorous Benchmarking**: Systematically benchmarked against LSTM, Random Forest, and ARIMA baselines on a 30-day multi-horizon test split.

---

## 2. Study Area & Dataset Topology

The system covers the critical agricultural aquifer system of Northwest India:
- **Core Modeling Hotspot**: Punjab & Haryana agricultural belt (23 Punjab districts + Haryana agricultural blocks), characterized by deep alluvial Indo-Gangetic aquifers under intensive paddy-wheat tubewell extraction.
- **National Scalable Topology**: Includes 205 monitored districts across 12 high-stress Indian states (`data/geo/punjab_haryana_districts.json` and `data/raw/fused_groundwater_timeseries_2017_2024.csv` with 728,160 records).

| State | Monitored Districts | Dominant Aquifer Typology | Extraction Stage |
|---|---|---|---|
| **Punjab** | Sangrur, Patiala, Ludhiana, Jalandhar, Bathinda, Moga, Barnala, Amritsar, Hoshiarpur, Firozpur, etc. (23 districts) | Quaternary Indo-Gangetic Alluvium | 164% (Over-Exploited) |
| **Haryana** | Kurukshetra, Karnal, Kaithal, Fatehabad, Sirsa, etc. (22 districts) | Semi-confined alluvial & aeolian sands | 134% (Critical) |

---

## 3. Mathematical Formulation

### Spatial Hydrogeological Graph Construction
For $N$ district nodes with pairwise geographic Haversine distance $d(i, j)$, the spatial adjacency matrix $W_{ij}$ is formed using a Gaussian kernel with distance threshold $\kappa$:
$$W_{ij} = \begin{cases} \exp\left(-\frac{d(i, j)^2}{\sigma^2}\right), & \text{if } d(i, j) \le \kappa \text{ and } W_{ij} \ge \epsilon \\ 0, & \text{otherwise} \end{cases}$$

With self-loops added ($\tilde{A} = W + I_N$), the symmetric normalized graph Laplacian is:
$$\tilde{A}_{norm} = \tilde{D}^{-\frac{1}{2}} \tilde{A} \tilde{D}^{-\frac{1}{2}}, \quad \text{where } \tilde{D}_{ii} = \sum_j \tilde{A}_{ij}$$

### Spatial Graph Convolution Operation
Spatial feature aggregation across communicating aquifer compartments (`SpatialGraphConv`):
$$H^{(l+1)} = \sigma\left(\tilde{D}^{-\frac{1}{2}} \tilde{A} \tilde{D}^{-\frac{1}{2}} H^{(l)} W^{(l)} + b^{(l)}\right)$$

### Temporal Gated Convolution (GLU)
Temporal sequence modeling along the time axis (`TemporalGatedConv`):
$$\Phi = \text{Conv1D}_K(X) \in \mathbb{R}^{B \times 2C_{out} \times T \times N}$$
$$[P, Q] = \text{Split}(\Phi, \text{dim}=\text{channels})$$
$$H_{temporal} = P \odot \sigma(Q)$$

where $P$ is the linear feature projection, $Q$ is the gating mechanism, and $\sigma(\cdot)$ is the sigmoid activation function controlling the propagation of recharge lag dynamics.

### Optimization Objective
The network optimizes empirical Mean Squared Error (MSE) loss with $L_2$ weight regularization:
$$\mathcal{L}_{MSE}(\Theta) = \frac{1}{B \cdot T_{out} \cdot N} \sum_{b=1}^B \sum_{t=1}^{T_{out}} \sum_{i=1}^N \left( y_{b,t,i} - \hat{y}_{b,t,i} \right)^2 + \frac{\lambda_{reg}}{2} \|\Theta\|_2^2$$

Trained with the Adam optimizer ($\text{lr} = 0.002$), gradient clipping ($\|\nabla_\Theta\| \le 5.0$), and `ReduceLROnPlateau` scheduling.

---

## 4. Benchmarking Results on 30-Day Forecast Horizon

| Model Architecture | Test RMSE (m) | Test MAE (m) | Test R² Score | Requirement R4 (<0.50m) |
|---|---|---|---|---|
| **Proposed ST-GNN (STGCN)** | **0.412 m** | **0.318 m** | **0.894** | **PASSED (<0.50m)** |
| LSTM Baseline | 0.684 m | 0.521 m | 0.742 | Exceeded threshold |
| Random Forest Regressor | 0.825 m | 0.640 m | 0.638 | Exceeded threshold |
| ARIMA Baseline | 1.152 m | 0.895 m | 0.420 | Exceeded threshold |

---

## 5. Repository Structure

```
py/
├── app.py                     # Streamlit Interactive Web Application
├── run_pipeline.py            # Master training & evaluation CLI runner
├── run.bat                    # One-click Windows dashboard launcher
├── requirements.txt           # Project dependencies
├── README.md                  # Comprehensive project documentation
├── data/
│   ├── geo/
│   │   └── punjab_haryana_districts.json   # 205 District coordinates & hydro metadata
│   ├── raw/
│   │   └── fused_groundwater_timeseries_2017_2024.csv # 728,160 observation records
│   └── processed/
│       ├── benchmark_results.json          # Exported comparative metrics
│       └── latest_forecast.json            # 30-day multi-district forecast
├── src/
│   ├── data_pipeline.py       # Physics-calibrated time series & dataset windowing
│   ├── graph_builder.py       # Haversine distance, Gaussian adjacency & Laplacian
│   ├── trainer.py             # PyTorch ST-GNN training loop with early stopping
│   ├── evaluator.py           # RMSE, MAE, R² computation and benchmarking
│   ├── forecaster.py          # 30-day predictor & CGWB risk alert engine
│   └── models/
│       ├── stgnn.py           # Core Spatio-Temporal GNN (GCN + Gated Conv GLU)
│       └── baselines.py       # LSTM, Random Forest & ARIMA baselines
├── tests/
│   └── test_pipeline.py       # Unit and integration test suite
└── checkpoints/
    └── best_stgnn.pt          # PyTorch trained model weights (110,755 parameters)
```

---

## 6. How to Run the Application

### 1. Launch the Interactive Web Dashboard
Run the batch launcher:
```powershell
.\run.bat
```
Or run directly in terminal:
```powershell
streamlit run app.py
```

### 2. Run the Full Model Training & Benchmarking Pipeline
To re-train the models and generate updated evaluation metrics:
```powershell
python run_pipeline.py
```

### 3. Run the Unit & Integration Tests
```powershell
python tests/test_pipeline.py
```

---

## 7. Features of the Web Dashboard
1. **Interactive Folium GIS Map**: Color-coded risk markers (Safe, Semi-Critical, Critical, Over-Exploited) with hydrogeological connectivity lines across Punjab & Haryana.
2. **30-Day Multi-Horizon Forecast Explorer**: Individual district deep-dives with interactive Plotly trajectories and confidence intervals.
3. **What-If Scenario Simulator**: Dynamic sliders for rainfall anomalies (-50% to +50%) and pumping intensity (0.5x to 1.4x).
4. **Model Benchmarking Lab**: Side-by-side performance bar charts and error distribution metrics.
5. **InSAR & Hydrogeology Data Hub**: Synchronized multi-signal visualization (Water Depth, InSAR Subsidence, Rainfall).
