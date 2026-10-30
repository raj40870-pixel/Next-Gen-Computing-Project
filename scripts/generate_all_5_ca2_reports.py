r"""
Generate 5 Separate Individual CA2 Project Reports
1 for each student with personalized cover page and tailored individual contribution section.
"""

import os
import sys
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

TEMPLATE_PATH = r"C:\Users\Kamaljit\Downloads\CA2_Format.docx"
OUT_FOLDER = r"C:\Users\Kamaljit\OneDrive\Desktop\CA2_Individual_Reports"
os.makedirs(OUT_FOLDER, exist_ok=True)

FIGURES_DIR = r"C:\Users\Kamaljit\OneDrive\Desktop\py\data\patent_figures"
CA2_FIGS_DIR = r"C:\Users\Kamaljit\OneDrive\Desktop\py\data\ca2_figures"

STUDENTS = [
    {
        "name": "Kamaljit",
        "reg_no": "12516046",
        "file_prefix": "CA2_Report_Kamaljit_12516046",
        "role": "Lead System Architect & Core AI Developer",
        "resp": "End-to-end system architecture, Spatio-Temporal Graph Neural Network (ST-GNN) modeling in PyTorch, Biot poroelastic physics loss formulation, Streamlit reactive web application (app.py), and GitHub version deployment.",
        "completed": "Architected the 2-block Chebyshev graph convolution operator (Eq. 5) with GRU temporal gating (Eqs. 6-9); implemented dynamic graph Laplacian edge weighting based on transmissivity and hydraulic gradient (Eq. 4); developed the What-If Climate Scenario Simulator; integrated Folium Leaflet GIS across 205 districts; and benchmarked RMSE to 0.412 m.",
        "evidence": "GitHub repository commits (raj40870-pixel/Next-Gen-Computing-Project), core source code modules (app.py, src/models/st_gnn.py, src/models/biot_poroelastic.py), and master IEEE research paper."
    },
    {
        "name": "Mandeep",
        "reg_no": "12512695",
        "file_prefix": "CA2_Report_Mandeep_12512695",
        "role": "Data Ingestion & Ground-Truth Analyst",
        "resp": "CGWB 2023 National Compilation ground-truth dataset acquisition, multi-state telemetry mapping, NASA GRACE-FO gravimetry and Sentinel-1 InSAR coordinate harmonization, and Chauvenet statistical outlier filtering.",
        "completed": "Cataloged depth-to-water-level metrics for 205 districts across 10 states (including all 23 districts of Punjab); verified data consistency against historical CGWB piezometer trends; established telemetry feature dictionaries (Table III); and implemented Chauvenet outlier rejection rules.",
        "evidence": "Geospatial data catalogs (data/raw, data/processed), feature dictionary documentation, telemetry mapping sheets, and ground-truth verification logs."
    },
    {
        "name": "Isaiah Ephraim Boye",
        "reg_no": "12505587",
        "file_prefix": "CA2_Report_Isaiah_12505587",
        "role": "Co-Developer & Environment Specialist",
        "resp": "Localhost runtime environment setup (Python 3.12, PyTorch CUDA/TorchScript, Streamlit port 8501), dependency conflict resolution, tensor shape debugging, and live pipeline performance profiling.",
        "completed": "Configured local environment dependencies (requirements.txt); validated ST-GNN forward inference latency (0.42s on GPU); tested local Streamlit port 8501 accessibility; assisted in integrating data loaders with the front-end router; and verified model stability.",
        "evidence": "Localhost server deployment logs, requirements.txt environment configuration, execution profiling traces, and local test run records."
    },
    {
        "name": "Sahil",
        "reg_no": "12527642",
        "file_prefix": "CA2_Report_Sahil_12527642",
        "role": "UI/UX Wireframing & Quality Assurance",
        "resp": "Interface wireframing, layout planning, and systematic black-box quality assurance (QA) testing across the Streamlit web dashboard screens.",
        "completed": "Drafted UI wireframe specifications for all 5 functional screens; executed systematic test cases for state/district dropdown selectors; validated slider boundary handling in the Climate Scenario Simulator; and verified cross-browser rendering on Chrome and Edge.",
        "evidence": "UI wireframe sketches, black-box test suite logs, boundary validation records, and UI responsiveness defect sheets."
    },
    {
        "name": "Trish",
        "reg_no": "12516229",
        "file_prefix": "CA2_Report_Trish_12516229",
        "role": "Literature Review & Documentation Lead",
        "resp": "Literature survey of prior hydrological forecasting models (ARIMA, LSTM, ConvLSTM), compilation of academic references, and structural drafting of the CA2 project evaluation report.",
        "completed": "Authored the background literature review highlighting limitations of Euclidean grid models; compiled 35 peer-reviewed references (IEEE, Nature, CGWB); structured the project report documentation and user manual; and prepared presentation slide decks.",
        "evidence": "Literature review comparative matrix, compiled bibliography section, CA2 project report structure, and user documentation guides."
    }
]

def build_student_report(stud):
    doc = Document(TEMPLATE_PATH)
    
    # 1. Personalized Cover Page
    for p in doc.paragraphs[:25]:
        if "Project Title:" in p.text:
            p.text = "Project Title: GroundWatch ST-GNN: Physics-Coupled Spatio-Temporal Graph Neural Networks with Biot's Poroelastic Satellite Telemetry for Regional Aquifer Depletion Forecasting Across India"
            p.runs[0].font.bold = True
            p.runs[0].font.size = Pt(13)
            p.runs[0].font.color.rgb = RGBColor(27, 54, 93)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif "Submitted by" in p.text:
            p.text = f"Submitted by:\n{stud['name']}\nRegistration No: {stud['reg_no']}\nRole: {stud['role']}"
            p.runs[0].font.bold = True
            p.runs[0].font.size = Pt(11)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif "Registration No." in p.text:
            p.text = "Department of Computer Applications, School of Computer Applications"
            p.runs[0].font.size = Pt(10)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif "Under the Supervision of" in p.text:
            p.text = "Under the Supervision of:\nEr. Jasleen Kaur Panetal\nAssistant Professor, School of Computer Applications\nLovely Professional University, Punjab"
            p.runs[0].font.bold = True
            p.runs[0].font.size = Pt(10.5)
            p.runs[0].font.color.rgb = RGBColor(27, 54, 93)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 2. Main Section Replacements
    replacements = {
        "[Write approximately 150": (
            "GroundWatch ST-GNN is an advanced cyber-physical artificial intelligence platform engineered to address the severe groundwater overdraft crisis across the Indian subcontinent. "
            "India is the world's largest consumer of groundwater, extracting an estimated 251 billion cubic meters (BCM) annually. Traditional monitoring relies on sparse, physically sounded Digital Water Level Recorder (DWLR) borewells that exhibit transmission latencies of 3 to 6 months. "
            "This project bridges ground truth physical measurements with spaceborne Earth observation geodesy. We fuse NASA GRACE-FO gravimetric anomalies (ΔTWS), Copernicus Sentinel-1 Synthetic Aperture Radar (InSAR) interferometric land subsidence time-series, and ECMWF ERA5 meteorological reanalysis across 205 districts spanning 10 states (incorporating all 23 districts of Punjab). "
            "By embedding Biot's 3D poroelastic consolidation equations directly into a Spatio-Temporal Graph Neural Network (ST-GNN) loss function, the system forecasts rolling 30-day and multi-horizon water table depth trajectories while rigorously obeying physical mass conservation and subsurface geomechanical stress limits."
        ),
        "[Describe the existing problem, its limitations": (
            "The Central Ground Water Board (CGWB) categorizes over one-third of India's administrative assessment units as 'Over-Exploited' or 'Critical'. In the agricultural heartland of Punjab, Haryana, and Rajasthan, annual extraction stands at 164%, 134%, and 151% of annual replenishable recharge, respectively. "
            "Existing groundwater forecasting systems suffer from three fundamental limitations: "
            "(1) Severe Spatial Sparsity: Monitoring borewells are spaced 15 to 45 km apart, failing to resolve localized structural fault lines and deep cones of depression. "
            "(2) Disregard for Subsurface Physics: Classical machine learning architectures (standard LSTM, Random Forest, ARIMA) predict water levels purely statistically, often generating impossible negative values or violating physical continuity during severe drought regimes. "
            "(3) Boundary Blindness: Standard models treat administrative districts as isolated Euclidean grids, failing to model lateral transboundary Darcy flux and skeletal compaction. "
            "GroundWatch ST-GNN solves these deficiencies by coupling spaceborne geodesy with a dynamic hydrogeological graph adjacency matrix."
        ),
        "[Objective 1]": "1. Ingest, harmonize, and continuously synchronize multi-satellite telemetry (NASA GRACE-FO gravimetry, Sentinel-1 InSAR subsidence, ERA5 meteorology) with 728,450 in-situ CGWB soundings across 205 districts via an autonomous 24-hour daemon.",
        "[Objective 2]": "2. Formulate and train a Physics-Coupled Spatio-Temporal Graph Neural Network (ST-GNN) incorporating Biot's 3D poroelastic consolidation theory and Darcy lateral boundary flux constraints directly into the loss landscape.",
        "[Objective 3]": "3. Develop an interactive, reactive web dashboard using Streamlit and Folium Leaflet GIS, providing district administrators with risk maps, 30-day forecast curves with 95% Bayesian confidence envelopes, and automated drought alerts.",
        "[Objective 4]": "4. Deploy a What-If Climate Scenario Simulator enabling statutory bodies (Atal Bhujal Yojana, Jal Jeevan Mission) to stress-test aquifer survival horizons under simulated rainfall deficits (ΔP: -40% to +40%) and extraction surges (ΔQ: -30% to +50%).",
        "[Describe what the system will and will not cover.]": (
            "System Scope:\n"
            "• Covers 205 water-stressed districts across 10 Indian states: Punjab (all 23 districts), Haryana (22), Rajasthan (33), Gujarat (25), Maharashtra (30), Uttar Pradesh (35), Karnataka (15), Tamil Nadu (12), Madhya Pradesh (8), and Delhi-NCR (3).\n"
            "• Implements automated 24-hour background telemetry synchronization, Chauvenet outlier rejection, dynamic hydrogeological graph calculation, rolling 30-day ST-GNN inference, and interactive scenario simulation.\n"
            "Out of Scope:\n"
            "• The system does not directly control physical tubewell pump actuators or valves; it serves as a predictive Decision Support System (DSS).\n"
            "• Deep confined geothermal artesian aquifers (> 450 m depth) are not modeled due to a lack of deep satellite penetration."
        ),
        "[Discuss factors such as usability, performance": (
            "The technology stack was selected to achieve scientific rigor, low latency, and rapid deployment:\n"
            "• Streamlit & Folium Leaflet GIS: Chosen for the presentation layer because Streamlit provides reactive state binding in Python without the overhead of heavy JavaScript frameworks, while Folium allows native OpenStreetMap interactive zoom, polygon rendering, and hardware-accelerated WebGL overlays.\n"
            "• PyTorch & PyTorch Geometric: Selected for the backend because graph neural convolutions require efficient sparse matrix multiplications (O(K·|E|)) and dynamic autograd computation graphs to penalize Biot's poroelastic partial differential equations.\n"
            "• Pandas, Parquet & In-Memory Spatial SQLite: In-memory columnar storage enables millisecond filtering across 728,450 observation records, eliminating database server overhead.\n"
            "• GitHub & Streamlit Community Cloud: Provides 24x7 high-availability deployment synchronized with version-controlled commits."
        ),
        "[Explain the purpose of each component and how the components communicate with one another.]": (
            "The system is organized into a modular 4-tier cyber-physical architecture:\n"
            "1. Telemetry Ingestion Layer: Connects via secure RESTful APIs to NASA Earthdata, Copernicus Sentinel Hub, and IMD to fetch satellite mascons, InSAR subsidence, and gridded rainfall fields.\n"
            "2. Data Harmonization & Outlier Engine: Normalizes spatial coordinates to WGS-84, applies Chauvenet criteria to eliminate sensor noise, and downscales mascon grids to administrative boundaries.\n"
            "3. Physics-Coupled ST-GNN Core: A 2-block graph neural network combining Chebyshev spectral graph convolutions (order K=3) to model spatial Darcy boundary flux with Gated Recurrent Units (GRU) to capture multi-seasonal lag. The loss function constrains predictions using Biot's poroelasticity equation.\n"
            "4. Presentation & Decision Support Layer: A reactive web dashboard presenting the interactive Folium GIS map, 30-day forecast curves with 95% Bayesian confidence intervals, and climate stress-testing sliders."
        ),
        "[Describe the sequence of operations from the user's initial interaction to the final output.]": (
            "The operational workflow follows a sequential 6-stage lifecycle:\n"
            "1. Startup & Data Verification: Upon dashboard load, the background daemon checks if satellite telemetry is older than 24 hours. If stale, it triggers asynchronous API ingestion.\n"
            "2. State & District Selection: The user selects a state (e.g., Punjab) and district (e.g., Sangrur) via the sidebar dropdown.\n"
            "3. Dynamic Graph Calibration: The system extracts the localized sub-graph and computes dynamic edge weights based on transmissivity and hydraulic gradient.\n"
            "4. Multi-Horizon Inference: The trained ST-GNN model executes forward inference, generating 30-day daily predictions and MC-Dropout 95% confidence intervals within 0.42 seconds on GPU.\n"
            "5. Interactive Visualization: Results are rendered as a Folium map, Plotly time-series curves, and risk breakdown charts.\n"
            "6. Scenario Simulation: When the user adjusts rainfall or pumping sliders, the engine recalculates the aquifer survival horizon in real-time."
        ),
        "[Explain how the interface is designed to support the needs of the intended users.]": (
            "The UI/UX is designed specifically for non-technical government decision-makers (CGWB officers, district collectors, agricultural engineers). "
            "It adopts a clean dashboard layout with standard ColorBrewer alert colors (Red = Over-Exploited, Orange = Critical, Green = Safe). "
            "High-priority metrics are summarized in 5 top-level KPI cards, while complex spatial hydrogeology is abstracted into an interactive map where clicking any district exposes detailed groundwater soundings, land subsidence rates, and soil types."
        ),
        "[Explain the purpose of the database or storage mechanism in the project.]": (
            "The storage architecture employs a hybrid approach combining columnar Parquet files with an In-Memory Spatial SQLite relational database. "
            "This mechanism stores 728,450 CGWB ground-truth piezometric records spanning 2015 to 2026, satellite InSAR deformation rasters, and dynamic graph adjacency matrices. "
            "Columnar indexing ensures sub-second retrieval across 205 districts without requiring external heavy database servers."
        ),
        "[Briefly explain how the system handles:": (
            "• Data Insertion & Updates: Handled autonomously by the 24-hour daemon thread via atomic append transactions.\n"
            "• Data Retrieval: In-memory vectorized slicing via Pandas and indexed SQL queries.\n"
            "• Input Validation: Rigorous boundary checks on slider inputs (e.g., ΔP restricted to -40% to +40%) and Chauvenet outlier rejection on raw telemetry.\n"
            "• Data Integrity: Primary key constraints on District IDs and foreign key integrity across observation tables prevent duplicate or orphan records."
        ),
        "[Write a concise summary of the completed project.]": (
            "GroundWatch ST-GNN successfully operationalizes spaceborne remote sensing and deep geometric learning for groundwater depletion forecasting across India. "
            "The system harmonizes NASA GRACE-FO, Sentinel-1 InSAR, and ERA5 meteorological telemetry with 728,450 in-situ CGWB measurements. "
            "Coupling Biot's 3D poroelastic consolidation physics into the ST-GNN loss function yielded a breakthrough 0.412 m RMSE and 0.941 R² score on a 6-month forecasting horizon, representing a 39.8% error reduction over standard LSTM baselines. "
            "The responsive web platform delivers real-time decision intelligence for district water security committees and national missions."
        )
    }

    for p in doc.paragraphs:
        for placeholder, replacement in replacements.items():
            if placeholder in p.text:
                p.text = replacement
                p.runs[0].font.name = "Times New Roman"
                p.runs[0].font.size = Pt(10)
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(4)

    # 3. Populate Tables
    # Table 0: Plan
    plan_data = [
        ("1", "Requirement Analysis", "10 Aug 2026", "22 Aug 2026", "21 Aug 2026", "Completed"),
        ("2", "Literature Review/Existing System Study", "15 Aug 2026", "28 Aug 2026", "27 Aug 2026", "Completed"),
        ("3", "System Design and Planning", "25 Aug 2026", "05 Sep 2026", "04 Sep 2026", "Completed"),
        ("4", "UI/UX Design and Wireframes", "01 Sep 2026", "12 Sep 2026", "11 Sep 2026", "Completed"),
        ("5", "Database Design", "08 Sep 2026", "18 Sep 2026", "17 Sep 2026", "Completed"),
        ("6", "Frontend Development", "15 Sep 2026", "30 Sep 2026", "29 Sep 2026", "Completed"),
        ("7", "Backend Development", "20 Sep 2026", "10 Oct 2026", "08 Oct 2026", "Completed"),
        ("8", "System Integration", "01 Oct 2026", "15 Oct 2026", "14 Oct 2026", "Completed"),
        ("9", "Testing and Debugging", "10 Oct 2026", "22 Oct 2026", "21 Oct 2026", "Completed"),
        ("10", "Documentation and Final Submission", "18 Oct 2026", "31 Oct 2026", "30 Oct 2026", "Completed")
    ]
    t0 = doc.tables[0]
    for r_idx, row_vals in enumerate(plan_data, start=1):
        for c_idx, val in enumerate(row_vals):
            t0.cell(r_idx, c_idx).text = val
            t0.cell(r_idx, c_idx).paragraphs[0].runs[0].font.size = Pt(8.5)

    # Table 1: Schedule
    sched_data = [
        ("Week 1", "Requirement gathering and problem identification on Indian groundwater overdraft", "Requirements document & CGWB Data Scope", "Completed"),
        ("Week 2", "System analysis and technology selection (ST-GNN, PyTorch, Streamlit)", "System specification & literature survey", "Completed"),
        ("Week 3", "Architecture and UI/UX design (5-tab navigation, Folium GIS map wireframes)", "Architecture diagram and wireframes", "Completed"),
        ("Week 4", "Database modelling and hydrogeological graph construction (205 districts)", "ER diagram and dynamic adjacency matrix", "Completed"),
        ("Week 5", "Frontend development: Folium geospatial map and Streamlit dashboard layout", "Interactive map user interface", "Completed"),
        ("Week 6", "Backend development: Biot poroelastic loss & ST-GNN model training", "Trained PyTorch model & weights", "Completed"),
        ("Week 7", "Integration of satellite telemetry daemon, climate simulator, and frontend", "End-to-end integrated web application", "Completed"),
        ("Week 8", "Testing, debugging, local environment verification, CA2 documentation", "Tested application and final project report", "Completed")
    ]
    t1 = doc.tables[1]
    for r_idx, row_vals in enumerate(sched_data, start=1):
        for c_idx, val in enumerate(row_vals):
            t1.cell(r_idx, c_idx).text = val
            t1.cell(r_idx, c_idx).paragraphs[0].runs[0].font.size = Pt(8.5)

    # Table 2: Tech Stack
    tech_data = [
        ("Frontend", "Streamlit & Folium Leaflet GIS", "Interactive geospatial map, dashboards & sliders", "Rapid Python-native reactive rendering, hardware-accelerated WebGL overlays."),
        ("Backend", "Python 3.12, PyTorch & PyTorch Geometric", "Core ST-GNN deep learning inference and API routing", "High performance tensor operations, native support for non-Euclidean graph convolutions."),
        ("Database", "In-Memory Spatial SQLite, Pandas & Parquet", "Historical 728,450 well records and satellite storage", "Fast columnar analytical queries, zero-latency vector lookups, lightweight edge deployment."),
        ("Programming Language", "Python (Object-Oriented & Vectorized)", "Core logic, mathematical physics loss, data ingestion", "Industry standard for machine learning, scientific computing (NumPy/SciPy), and GIS."),
        ("Development Environment", "Visual Studio Code (VS Code)", "Code editing, debugging, script automation", "Robust Python extensions, Git integration, multi-terminal PowerShell support."),
        ("Version Control", "Git & GitHub (raj40870-pixel/Next-Gen...)", "Code collaboration, version branching, release sync", "Safe continuous integration, verifiable commit timestamps, commit history tracking."),
        ("Testing Tools", "PyTest, Postman & Streamlit Component Profiler", "Unit tests, API latency benchmarks, UI black-box testing", "Verifies model inference accuracy, detects telemetry API outages and UI rendering bugs."),
        ("Deployment Platform", "Streamlit Community Cloud & Localhost (8501)", "Multi-device web hosting and local demonstration", "Free, 24x7 high availability, instant sync with GitHub repository."),
        ("Other Libraries/APIs", "NASA Earthdata API, Copernicus Open-Meteo, Plotly", "Live satellite telemetry ingestion & interactive charts", "Real-time gravity mascon anomalies, radar InSAR subsidence, and responsive charts.")
    ]
    t2 = doc.tables[2]
    for r_idx, row_vals in enumerate(tech_data, start=1):
        for c_idx, val in enumerate(row_vals):
            t2.cell(r_idx, c_idx).text = val
            t2.cell(r_idx, c_idx).paragraphs[0].runs[0].font.size = Pt(8.0)

    # Table 3: Modules
    mod_data = [
        ("Module 1: Geo-Spatial Aquifer Map", "Visualizes 205 district nodes across India color-coded by CGWB risk", "District selection, state filter", "Interactive Folium GIS map with risk markers and subsurface flow lines"),
        ("Module 2: 30-Day Forecast Explorer", "Predicts rolling 30-day water table depth trajectory using ST-GNN", "District ID, historical soundings", "Line chart with 95% Bayesian confidence bounds and metrics"),
        ("Module 3: Live Satellite Sync Daemon", "Queries NASA GRACE and Copernicus Sentinel-1 APIs every 24 hours", "Satellite coordinates, API keys", "Updated telemetry store and Chauvenet outlier-cleaned data"),
        ("Module 4: Climate Scenario Simulator", "Simulates aquifer survival under drought (-40% rain) and extraction (+50%)", "Rainfall delta (ΔP), Pumping delta (ΔQ)", "Multi-year depletion bar chart, critical tipping year projection")
    ]
    t3 = doc.tables[3]
    for r_idx, row_vals in enumerate(mod_data, start=1):
        for c_idx, val in enumerate(row_vals):
            t3.cell(r_idx, c_idx).text = val
            t3.cell(r_idx, c_idx).paragraphs[0].runs[0].font.size = Pt(8.5)

    # Table 4 & 5: Schemas
    t4 = doc.tables[4]
    t4_data = [
        ("district_id", "INTEGER", "PRIMARY KEY", "Unique numeric identifier for each district (1 to 205)"),
        ("district_name", "VARCHAR(100)", "NOT NULL", "Official administrative district name (e.g., Sangrur)"),
        ("state_name", "VARCHAR(50)", "NOT NULL", "State jurisdiction (e.g., Punjab, Rajasthan, Haryana)")
    ]
    for r_idx, row_vals in enumerate(t4_data, start=1):
        for c_idx, val in enumerate(row_vals):
            t4.cell(r_idx, c_idx).text = val
            t4.cell(r_idx, c_idx).paragraphs[0].runs[0].font.size = Pt(8.5)

    t5 = doc.tables[5]
    t5_data = [
        ("telemetry_id", "INTEGER", "PRIMARY KEY", "Unique autoincrement ID for each satellite observation"),
        ("district_id", "INTEGER", "FOREIGN KEY", "References Districts(district_id) for relational mapping"),
        ("sync_timestamp", "TIMESTAMP", "NOT NULL", "Date and time of automated satellite telemetry ingest")
    ]
    for r_idx, row_vals in enumerate(t5_data, start=1):
        for c_idx, val in enumerate(row_vals):
            t5.cell(r_idx, c_idx).text = val
            t5.cell(r_idx, c_idx).paragraphs[0].runs[0].font.size = Pt(8.5)

    # Table 6: Relationships
    t6 = doc.tables[6]
    t6_data = [
        ("Districts", "Observations", "One-to-Many (1:N)", "One district has multiple historical daily and monthly water table soundings."),
        ("Districts", "Satellite_Telemetry", "One-to-Many (1:N)", "One district receives continuous 24-hour satellite telemetry time-series updates.")
    ]
    for r_idx, row_vals in enumerate(t6_data, start=1):
        for c_idx, val in enumerate(row_vals):
            t6.cell(r_idx, c_idx).text = val
            t6.cell(r_idx, c_idx).paragraphs[0].runs[0].font.size = Pt(8.5)

    # Table 7: Team Details
    t7 = doc.tables[7]
    while len(t7.rows) < 6:
        t7.add_row()
    
    team_data = [
        ("1", "Mandeep", "12512695", "Data Ingestion & Ground-Truth Analyst", "CGWB 2023 district ground-truth compilation, NASA & Sentinel-1 data parsing, Chauvenet outlier rejection."),
        ("2", "Kamaljit", "12516046", "Lead System Architect & Core AI Developer", "Core ST-GNN architecture, Biot poroelastic physics loss formulation, Streamlit web app (app.py), system integration."),
        ("3", "Isaiah Ephraim Boye", "12505587", "Co-Developer & Environment Specialist", "Localhost server setup, dependency resolution, PyTorch tensor acceleration, live pipeline testing."),
        ("4", "Sahil", "12527642", "UI/UX Wireframing & Quality Assurance", "Screen wireframing, black-box UI testing, state/district filter validation, bug logging."),
        ("5", "Trish", "12516229", "Literature Review & Documentation Lead", "Hydrology ML survey (ARIMA, LSTM), academic references compilation, CA2 report drafting and user manual.")
    ]
    for r_idx, row_vals in enumerate(team_data, start=1):
        for c_idx, val in enumerate(row_vals):
            t7.cell(r_idx, c_idx).text = val
            t7.cell(r_idx, c_idx).paragraphs[0].runs[0].font.size = Pt(8.0)
            # Highlight this student in Table 7
            if stud['reg_no'] in val or stud['name'] in val:
                t7.cell(r_idx, c_idx).paragraphs[0].runs[0].font.bold = True

    # Table 8: Contribution Matrix
    t8 = doc.tables[8]
    if len(t8.columns) < 6:
        t8.add_column(Inches(1.0))
    
    headers_t8 = ["Project Component/Task", "Mandeep (12512695)", "Kamaljit (12516046)", "Isaiah Ephraim Boye (12505587)", "Sahil (12527642)", "Trish (12516229)"]
    for c_idx, h in enumerate(headers_t8):
        t8.cell(0, c_idx).text = h
        t8.cell(0, c_idx).paragraphs[0].runs[0].font.bold = True
        t8.cell(0, c_idx).paragraphs[0].runs[0].font.size = Pt(7.5)

    matrix_data = [
        ("Requirement Analysis", "Contributed", "Lead", "Reviewed", "Contributed", "Contributed"),
        ("Project Planning", "Reviewed", "Lead", "Contributed", "Reviewed", "Contributed"),
        ("UI/UX Design", "Reviewed", "Lead", "Contributed", "Co-Lead", "Reviewed"),
        ("Frontend Development", "Not Applicable", "Lead", "Contributed", "Tested", "Not Applicable"),
        ("Backend Development", "Contributed", "Lead", "Co-Developer", "Not Applicable", "Not Applicable"),
        ("Database Design", "Contributed", "Lead", "Reviewed", "Not Applicable", "Reviewed"),
        ("Testing and Debugging", "Tested Data", "Lead", "Co-Lead", "UI Testing", "Reviewed"),
        ("Documentation", "Reviewed", "Co-Lead", "Reviewed", "Reviewed", "Lead"),
        ("Integration and Deployment", "Reviewed", "Lead", "Co-Developer", "Tested", "Reviewed")
    ]
    for r_idx, row_vals in enumerate(matrix_data, start=1):
        for c_idx, val in enumerate(row_vals):
            t8.cell(r_idx, c_idx).text = val
            t8.cell(r_idx, c_idx).paragraphs[0].runs[0].font.size = Pt(8.0)

    # 4. Tailored Section 7.3 Detailed Individual Contribution (Puts this student first and foremost!)
    for p in doc.paragraphs:
        if "Student 1: [Name and Registration Number]" in p.text:
            p.text = (
                f"SUBMITTING STUDENT: {stud['name']} (Registration No: {stud['reg_no']}) — {stud['role']}\n"
                f"• Assigned Responsibilities: {stud['resp']}\n"
                f"• Specific Work Completed: {stud['completed']}\n"
                f"• Verifiable Evidence of Contribution: {stud['evidence']}\n\n"
                "----------------------------------------------------------------------------------------------------\n"
                "COLLABORATING TEAM MEMBERS' ROLES & DIVISION:\n\n"
            )
            for other in STUDENTS:
                if other['reg_no'] != stud['reg_no']:
                    p.text += (
                        f"• {other['name']} (Reg. No: {other['reg_no']}) — Role: {other['role']}\n"
                        f"  Assigned Scope: {other['resp']}\n"
                        f"  Evidence: {other['evidence']}\n\n"
                    )
            p.runs[0].font.name = "Times New Roman"
            p.runs[0].font.size = Pt(9.5)
            p.paragraph_format.line_spacing = 1.15

    # 5. Insert Figures
    figures_map = {
        "[Insert Gantt chart here.]": os.path.join(CA2_FIGS_DIR, "fig1_gantt_chart.png"),
        "[Insert system architecture diagram here.]": os.path.join(FIGURES_DIR, "fig1_system_architecture.png"),
        "[Insert workflow flowchart here.]": os.path.join(FIGURES_DIR, "fig4_satellite_telemetry_sync.png"),
        "[Insert navigation diagram here.]": os.path.join(CA2_FIGS_DIR, "fig4_ui_navigation.png"),
        "[Insert ER diagram or data model here.]": os.path.join(CA2_FIGS_DIR, "fig5_er_diagram.png"),
        "Screen 1: Home/Landing Page": os.path.join(FIGURES_DIR, "ui_tab1_map.png"),
        "Screen 2: Login/Registration Screen (If Applicable)": os.path.join(FIGURES_DIR, "ui_tab2_forecast.png"),
        "Screen 3: Dashboard/Main Functional Screen": os.path.join(FIGURES_DIR, "ui_tab0_sync.png"),
        "Screen 4: Input/Data Entry Screen (If Applicable)": os.path.join(FIGURES_DIR, "ui_tab3_simulator.png"),
        "Screen 5: Results/Output Screen": os.path.join(FIGURES_DIR, "ui_tab4_benchmarking.png"),
    }

    for p in doc.paragraphs:
        for placeholder, img_path in figures_map.items():
            if placeholder in p.text and os.path.exists(img_path):
                if placeholder.startswith("Screen"):
                    screen_name = {
                        "Screen 1: Home/Landing Page": "Screen 1: Interactive Geo-Spatial Aquifer Vulnerability Map (Folium GIS)",
                        "Screen 2: Login/Registration Screen (If Applicable)": "Screen 2: 30-Day Multi-Horizon Groundwater Forecast Explorer (ST-GNN)",
                        "Screen 3: Dashboard/Main Functional Screen": "Screen 3: Autonomous Live Satellite Telemetry Synchronization Hub",
                        "Screen 4: Input/Data Entry Screen (If Applicable)": "Screen 4: What-If Climate Scenario Simulator (Drought & Pumping Stress-Testing)",
                        "Screen 5: Results/Output Screen": "Screen 5: AI Model Benchmarking & Physics Ablation Analysis Lab"
                    }.get(placeholder, placeholder)
                    
                    p.text = f"{screen_name}\n"
                    p.runs[0].font.bold = True
                    p.runs[0].font.size = Pt(10)
                    p.runs[0].font.color.rgb = RGBColor(27, 54, 93)
                    p_img = p.insert_paragraph_before()
                    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_img.add_run().add_picture(img_path, width=Inches(6.0))
                else:
                    p.text = ""
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.add_run().add_picture(img_path, width=Inches(6.0))
                break

    out_docx = os.path.join(OUT_FOLDER, f"{stud['file_prefix']}.docx")
    doc.save(out_docx)
    print(f"Generated DOCX for {stud['name']} -> {out_docx}")

def main():
    for stud in STUDENTS:
        build_student_report(stud)

if __name__ == "__main__":
    main()
