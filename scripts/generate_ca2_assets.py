import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
import pandas as pd
import datetime
import os

os.makedirs(r"C:\Users\Kamaljit\OneDrive\Desktop\py\data\ca2_figures", exist_ok=True)
OUT_DIR = r"C:\Users\Kamaljit\OneDrive\Desktop\py\data\ca2_figures"

# ----------------------------------------------------------------------
# 1. GANTT CHART (Figure 1)
# ----------------------------------------------------------------------
def generate_gantt_chart():
    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
    
    tasks = [
        ("1. Requirement & Literature Study", "2026-08-10", "2026-08-22", "#1e3a8a"),
        ("2. Geospatial Dataset Ingestion", "2026-08-20", "2026-09-05", "#0284c7"),
        ("3. UI/UX Wireframing & Design", "2026-09-01", "2026-09-12", "#0d9488"),
        ("4. Hydrogeological Graph Modeling", "2026-09-08", "2026-09-22", "#16a34a"),
        ("5. ST-GNN Core & Physics Loss", "2026-09-18", "2026-10-05", "#d97706"),
        ("6. Streamlit Frontend Integration", "2026-09-28", "2026-10-14", "#dc2626"),
        ("7. Localhost & Satellite Sync QA", "2026-10-08", "2026-10-22", "#9333ea"),
        ("8. CA2 Evaluation & Documentation", "2026-10-18", "2026-10-31", "#475569")
    ]
    
    y_ticks = []
    y_labels = []
    
    for idx, (task, start_s, end_s, color) in enumerate(tasks):
        start = datetime.datetime.strptime(start_s, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_s, "%Y-%m-%d")
        duration = (end - start).days
        y = len(tasks) - idx
        y_ticks.append(y)
        y_labels.append(task)
        ax.barh(y, duration, left=start, height=0.55, align='center', color=color, alpha=0.9, edgecolor='black', linewidth=0.8)
        ax.text(start + datetime.timedelta(days=1), y, f"{duration}d", va='center', ha='left', color='white', fontweight='bold', fontsize=8)

    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, fontsize=9, fontweight='semibold')
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.set_xlabel("Project Timeline (August 2026 – October 2026)", fontsize=10, fontweight='bold', labelpad=8)
    ax.set_title("GroundWatch ST-GNN: 8-Week Project Development Schedule & Milestones", fontsize=12, fontweight='bold', pad=12, color="#1e3a8a")
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    out_path = os.path.join(OUT_DIR, "fig1_gantt_chart.png")
    plt.savefig(out_path, bbox_inches='tight')
    plt.close()
    print("Gantt Chart saved to:", out_path)

# ----------------------------------------------------------------------
# 2. UI NAVIGATION DIAGRAM (Figure 4)
# ----------------------------------------------------------------------
def generate_nav_diagram():
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    # Root / Sidebar Node
    sidebar = patches.FancyBboxPatch((0.5, 2.0), 2.2, 2.0, boxstyle="round,pad=0.2", facecolor="#1e3a8a", edgecolor="#0f172a", linewidth=1.5)
    ax.add_patch(sidebar)
    ax.text(1.6, 3.2, "Navigation Sidebar\n(app.py)", color="white", weight="bold", fontsize=10, ha="center")
    ax.text(1.6, 2.4, "• State Selection\n• Satellite Status\n• Tab Router", color="#93c5fd", fontsize=8, ha="center")

    screens = [
        ("Screen 1: Geo-Spatial Map", "Folium GIS & 205 Districts\nCGWB Stress Nodes & Edges", 5.0, 5.0, "#0284c7"),
        ("Screen 2: 30-Day Forecast", "ST-GNN Multi-Horizon Line\n95% Bayesian Confidence Band", 5.0, 3.8, "#0d9488"),
        ("Screen 3: Live Satellite Sync", "NASA GRACE-FO & InSAR\n24-hr Background Daemon", 5.0, 2.6, "#16a34a"),
        ("Screen 4: Climate Simulator", "What-If Drought & Pumping\nRCP Scenario Stress-Testing", 5.0, 1.4, "#d97706"),
        ("Screen 5: Benchmarking Lab", "RMSE / R2 vs LSTM / ARIMA\nAblation Analysis Dashboard", 5.0, 0.2, "#dc2626"),
    ]
    
    for title, desc, x, y, color in screens:
        box = patches.FancyBboxPatch((x, y - 0.35), 4.2, 0.9, boxstyle="round,pad=0.15", facecolor="#f8fafc", edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(x + 0.2, y + 0.18, title, color=color, weight="bold", fontsize=9)
        ax.text(x + 0.2, y - 0.15, desc, color="#475569", fontsize=7.5)
        # Arrow from sidebar
        ax.annotate("", xy=(x, y + 0.1), xytext=(2.9, 3.0),
                    arrowprops=dict(arrowstyle="->", color="#64748b", lw=1.5, connectionstyle="arc3,rad=0.08"))

    ax.set_title("GroundWatch ST-GNN: Hierarchical UI Navigation & Modular Screen Routing", fontsize=11, fontweight="bold", pad=10, color="#1e3a8a")
    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "fig4_ui_navigation.png")
    plt.savefig(out_path, bbox_inches='tight')
    plt.close()
    print("UI Navigation Diagram saved to:", out_path)

# ----------------------------------------------------------------------
# 3. ENTITY RELATIONSHIP DIAGRAM (Figure 5)
# ----------------------------------------------------------------------
def generate_er_diagram():
    fig, ax = plt.subplots(figsize=(10.5, 5.5), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    entities = [
        ("DISTRICTS (Master)", ["PK: district_id (INT)", "district_name (VARCHAR)", "state_name (VARCHAR)", "latitude, longitude (FLOAT)", "aquifer_type (VARCHAR)", "baseline_depth_mbgl (FLOAT)"], 0.8, 3.2, "#1e3a8a"),
        ("OBSERVATIONS (Historical)", ["PK: obs_id (INT)", "FK: district_id (INT)", "obs_date (DATE)", "dwlr_depth_mbgl (FLOAT)", "cgwb_status (VARCHAR)"], 4.2, 3.2, "#0284c7"),
        ("SATELLITE_TELEMETRY (Sync)", ["PK: telemetry_id (INT)", "FK: district_id (INT)", "sync_timestamp (TIMESTAMP)", "grace_tws_cm (FLOAT)", "insar_subsidence_mm (FLOAT)", "rainfall_mm (FLOAT)"], 7.6, 3.2, "#0d9488"),
        ("FORECAST_RESULTS (AI)", ["PK: forecast_id (INT)", "FK: district_id (INT)", "horizon_days (INT)", "predicted_depth_mbgl (FLOAT)", "ci_lower_95, ci_upper_95 (FLOAT)"], 4.2, 0.4, "#d97706")
    ]
    
    for title, fields, x, y, color in entities:
        box = patches.FancyBboxPatch((x, y), 2.7, 2.2, boxstyle="round,pad=0.15", facecolor="#ffffff", edgecolor=color, linewidth=2)
        ax.add_patch(box)
        header = patches.FancyBboxPatch((x, y + 1.7), 2.7, 0.5, boxstyle="round,pad=0.08", facecolor=color, edgecolor=color, linewidth=1)
        ax.add_patch(header)
        ax.text(x + 1.35, y + 1.95, title, color="white", weight="bold", fontsize=8.5, ha="center")
        
        for f_idx, field in enumerate(fields):
            weight = "bold" if "PK:" in field or "FK:" in field else "normal"
            f_color = "#b91c1c" if "PK:" in field else ("#0369a1" if "FK:" in field else "#334155")
            ax.text(x + 0.15, y + 1.45 - (f_idx * 0.26), field, color=f_color, fontsize=7.5, weight=weight)

    # Relationship Connectors
    # Districts -> Observations (1:N)
    ax.annotate("1 : N", xy=(4.2, 4.3), xytext=(3.5, 4.3),
                arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.5))
    # Districts -> Satellite Telemetry (1:N)
    ax.annotate("1 : N", xy=(7.6, 4.3), xytext=(6.9, 4.3),
                arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.5))
    # Districts -> Forecast Results (1:N)
    ax.annotate("1 : N", xy=(4.2, 2.0), xytext=(2.2, 3.2),
                arrowprops=dict(arrowstyle="->", color="#334155", lw=1.5, connectionstyle="arc3,rad=-0.2"))

    ax.set_title("GroundWatch ST-GNN: Relational Data Schema & Entity-Relationship (ER) Architecture", fontsize=11, fontweight="bold", pad=12, color="#1e3a8a")
    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "fig5_er_diagram.png")
    plt.savefig(out_path, bbox_inches='tight')
    plt.close()
    print("ER Diagram saved to:", out_path)

if __name__ == "__main__":
    generate_gantt_chart()
    generate_nav_diagram()
    generate_er_diagram()
