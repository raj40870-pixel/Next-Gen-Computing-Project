# Groundwater Depletion Forecasting Using Satellite InSAR and Rainfall Data Fusion: A Spatio-Temporal Graph Neural Network (ST-GNN) Approach

---

## 1. Executive Summary & Problem Overview
Groundwater constitutes ~30% of global freshwater and is the bedrock of agricultural irrigation in Northwest India (Punjab & Haryana). Excessive irrigation pumping, coupled with delayed monsoon replenishment, has caused water table declines of **0.5 to 1.0 metres per year**, with over 78% of assessment blocks classified as **Over-Exploited** by the Central Ground Water Board (CGWB).

### The Scientific Innovation
Conventional monitoring relies on sparse observation boreholes and low-resolution GRACE gravity satellites (~300 km resolution). This system presents an end-to-end framework combining:
1. **Sentinel-1 C-Band InSAR (Interferometric Synthetic Aperture Radar)**: Millimeter-scale surface deformation time-series (SBAS technique) serving as a physical proxy for aquifer compaction and volume loss.
2. **IMD Gridded Rainfall & CHIRPS Precipitation**: Capturing monsoon percolation dynamics and time-lagged aquifer recharge.
3. **Spatio-Temporal Graph Neural Network (ST-GNN)**: 
   - **Spatial Graph Convolutions**: Encodes 15 monitoring district zones as graph nodes with Gaussian distance thresholded edges capturing lateral aquifer seepage and hydrostatic pressure equilibrium.
   - **Gated Temporal Convolutions (TCN)**: Models multi-step seasonal extraction patterns and delayed precipitation infiltration.
4. **Comparative Benchmarking**: Benchmarked against LSTM, ARIMA, and Random Forest baselines.

---

## 2. Study Area: 15 Agricultural Districts

| State | Districts Covered | Hydrogeological Regime |
|---|---|---|
| **Punjab** | Sangrur, Patiala, Ludhiana, Jalandhar, Bathinda, Moga, Barnala, Amritsar, Hoshiarpur, Firozpur | Indo-Gangetic Alluvial, heavy paddy-wheat rotation, deep tubewell extraction |
| **Haryana** | Kurukshetra, Karnal, Kaithal, Fatehabad, Sirsa | Semi-confined alluvial aquifers, high water stress, Ghaggar/Yamuna basin |

---

## 3. Mathematical Formulation

### Spatial Hydrogeological Graph Construction
For $N = 15$ district nodes, the pairwise geographic haversine distance is $d(i, j)$. The hydrogeological adjacency matrix $W_{ij}$ is formed using a Gaussian kernel with spatial thresholding:
$$W_{ij} = \begin{cases} \exp\left(-\frac{d(i, j)^2}{\sigma^2}\right), & \text{if } d(i, j) \le \kappa \text{ and } W_{ij} \ge \epsilon \\ 0, & \text{otherwise} \end{cases}$$
With self-loops added ($\tilde{A} = W + I_N$), the symmetric normalized graph Laplacian is:
$$\tilde{L}_{sym} = \tilde{D}^{-\frac{1}{2}} \tilde{A} \tilde{D}^{-\frac{1}{2}}, \quad \text{where } \tilde{D}_{ii} = \sum_j \tilde{A}_{ij}$$

### Graph Convolution Operation
Spatial feature aggregation across adjacent aquifers:
$$H^{(l+1)} = \sigma\left(\tilde{D}^{-\frac{1}{2}} \tilde{A} \tilde{D}^{-\frac{1}{2}} H^{(l)} W^{(l)} + b^{(l)}\right)$$

---

## 4. Benchmarking Results on 30-Day Forecast Horizon

| Model Architecture | Test RMSE (m) | Test MAE (m) | Test R² Score | Requirement R4 (<0.50m) |
|---|---|---|---|---|
| **Proposed ST-GNN** | **0.412 m** | **0.318 m** | **0.894** | **PASSED (Achieved <0.50m)** |
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
│   │   └── punjab_haryana_districts.json   # 15 District coordinates & metadata
│   ├── raw/
│   │   └── fused_groundwater_timeseries_2017_2024.csv # Multi-year observations
│   └── processed/
│       ├── benchmark_results.json          # Exported comparative metrics
│       └── latest_forecast.json            # 30-day multi-district forecast
├── src/
│   ├── data_pipeline.py       # Time-series ingestion, alignment & normalization
│   ├── graph_builder.py       # Distance matrix, Gaussian adjacency & Laplacian
│   ├── trainer.py             # PyTorch ST-GNN training loop with early stopping
│   ├── evaluator.py           # RMSE, MAE, R² computation and benchmarking
│   ├── forecaster.py          # 30-day predictor & CGWB risk alert engine
│   └── models/
│       ├── stgnn.py           # Core Spatio-Temporal Graph Neural Network
│       └── baselines.py       # LSTM, Random Forest & ARIMA baselines
├── tests/
│   └── test_pipeline.py       # Unit and integration test suite
└── checkpoints/
    └── best_stgnn.pt          # PyTorch trained model weights
```

---

## 6. How to Run the Application

### 1. Launch the Interactive Web Dashboard
Run the one-click batch launcher:
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
