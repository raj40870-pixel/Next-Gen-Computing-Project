r"""
Generate Clean, Professional Team Task Allocation Document
No hierarchy/team leader labels.
Strictly: Project Title, Member Name, Assigned Topics & Research Scope.
"""

import os
import sys
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

DOCX_PATH = r"C:\Users\Kamaljit\Downloads\Team_Task_Allocation.docx"

NAVY = RGBColor(27, 54, 93)       # #1B365D
DARK_GRAY = RGBColor(60, 60, 60)
CHARCOAL = RGBColor(34, 34, 34)
ACCENT_BLUE = RGBColor(0, 102, 204)

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=160, right=160):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'  <w:top w:w="{top}" w:type="dxa"/>'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'  <w:left w:w="{left}" w:type="dxa"/>'
        f'  <w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_card_borders(table, border_color="1B365D"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="none"/>'
        f'  <w:bottom w:val="none"/>'
        f'  <w:left w:val="single" w:sz="18" w:space="0" w:color="{border_color}"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideH w:val="none"/>'
        f'  <w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def build_allocation_doc():
    doc = Document()

    # Standard Margins
    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    # Document Header / Project Title
    p_proj = doc.add_paragraph()
    p_proj.paragraph_format.space_before = Pt(0)
    p_proj.paragraph_format.space_after = Pt(2)
    p_proj.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_label = p_proj.add_run("PROJECT RESEARCH & DEFENSE TASK ALLOCATION")
    r_label.font.name = "Segoe UI"
    r_label.font.size = Pt(11)
    r_label.font.bold = True
    r_label.font.color.rgb = ACCENT_BLUE

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(8)
    p_title.paragraph_format.line_spacing = 1.15
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("Deep Spatio-Temporal Graph Neural Networks Coupled with Biot's Poroelastic Satellite Telemetry for Regional Aquifer Depletion Forecasting Across India")
    r_title.font.name = "Segoe UI"
    r_title.font.size = Pt(15)
    r_title.font.bold = True
    r_title.font.color.rgb = NAVY

    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_before = Pt(0)
    p_div.paragraph_format.space_after = Pt(14)
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_div = p_div.add_run("―" * 55)
    r_div.font.name = "Segoe UI"
    r_div.font.size = Pt(10)
    r_div.font.color.rgb = RGBColor(180, 190, 205)

    members_data = [
        {
            "num": "1",
            "name": "Kamaljit",
            "topic": "System Architecture, Poroelastic Consolidation Physics & Loss Formulation",
            "sections": "Section I (Introduction & Crisis Overview), Section III (B, F - Biot's Poroelasticity & Loss Equations 2, 3, 10), Section X (Conclusion)",
            "scope": [
                "Understand the core problem: India's 251 BCM annual groundwater overdraft, critical depletion in Punjab (164%), Rajasthan (151%), and Haryana (134%).",
                "Explain Biot's 3D Poroelastic Theory: How water extraction lowers pore pressure and causes land subsidence (Eq. 3: Delta_h = 1/S_sk * Delta_z).",
                "Explain the composite Loss Function: Combining empirical prediction error (MSE), Biot geomechanical penalty, and Darcy mass balance conservation."
            ]
        },
        {
            "num": "2",
            "name": "Mandeep",
            "topic": "Multi-Source Satellite Telemetry, Datasets & Ingestion Pipeline",
            "sections": "Section I (C - Spaceborne Geodesy), Section IV (Algorithm 1 - Autonomous Telemetry Daemon), Section V (Geospatial Dataset Engineering, Tables II & III)",
            "scope": [
                "Understand the 4 data streams: NASA GRACE-FO (gravity anomalies), Copernicus Sentinel-1 (InSAR subsidence), ECMWF ERA5 (rainfall, temperature, PET), and CGWB (728,450 well records across 205 districts).",
                "Explain the 24-hour background synchronization daemon (Algorithm 1) and Chauvenet outlier rejection.",
                "Detail the spatial and temporal resolution differences between satellite feeds and in-situ monitoring stations."
            ]
        },
        {
            "num": "3",
            "name": "Isaiah",
            "topic": "AI/ML Graph Architecture: Spatio-Temporal Graph Neural Network (ST-GNN)",
            "sections": "Section III (C, D, E - Dynamic Graph Construction, Chebyshev Spectral Convolutions, GRU Equations 4-9), Section IV (Algorithm 2), Section XI (Computational Complexity)",
            "scope": [
                "Explain why Graph Neural Networks are needed: Irregular hydrogeological basins and lateral transboundary flow cannot be modeled by standard 2D CNNs or LSTMs.",
                "Explain the Dynamic Graph Adjacency Matrix (Eq. 4): How edge weights are calculated from hydraulic conductivity (transmissivity) and head gradients.",
                "Explain Chebyshev Spectral Convolutions (order K=3) and how localized graph filtering achieves fast inference in 0.42 seconds on GPU."
            ]
        },
        {
            "num": "4",
            "name": "Sahil",
            "topic": "Model Benchmarking, Experimental Evaluation & Ablation Analysis",
            "sections": "Section II (Literature Review, Table I), Section VI (A, B - Performance Benchmarking, Tables IV & V), Section XI (B - Bayesian Uncertainty Quantification)",
            "scope": [
                "Present the benchmarking results: ST-GNN (RMSE = 0.412 m, R² = 0.941) beats LSTM (RMSE = 0.684 m) by 39.8% and ARIMA (RMSE = 1.152 m) by 64.2%.",
                "Explain the Ablation Study (Table V): Removing Biot physics increases error by +18.9%, removing Darcy flux increases error by +11.2%, and using static k-NN graph increases error by +27.2%.",
                "Explain Monte Carlo Dropout (M=50) and how 95% Bayesian confidence intervals are generated for predictions."
            ]
        },
        {
            "num": "5",
            "name": "Krishna",
            "topic": "Regional Hydrogeology, Basin Depletion & Climate Scenario Simulation",
            "sections": "Section I (A - Regional Hydrogeology), Section VI (C, D - 5 Geological Regimes & Punjab-Haryana Analysis), Section VII (Climate Stress Simulation & Policy Missions), Section XII (NISAR Roadmap)",
            "scope": [
                "Understand regional aquifer differences: Indo-Gangetic Quaternary alluvium vs Peninsular hard-rock basalt vs Arid Rajasthan sandstones.",
                "Analyze the Punjab-Haryana crisis: Tubewell density > 38/km², localized depression cones, and irreversible loss of 14% aquifer storage volume.",
                "Explain the Climate Stress Simulator: Testing severe drought (-30% rain, +20% pumping) and showing real-world policy support for Atal Bhujal Yojana (ATAL JAL) and Jal Jeevan Mission."
            ]
        }
    ]

    for item in members_data:
        # Create a card table
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        tbl.columns[0].width = Inches(6.9)

        cell = tbl.cell(0, 0)
        cell.width = Inches(6.9)
        set_cell_background(cell, "F7F9FC")
        set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
        set_card_borders(tbl, "1B365D")

        # Member Header
        p_mh = cell.paragraphs[0]
        p_mh.paragraph_format.space_before = Pt(0)
        p_mh.paragraph_format.space_after = Pt(2)
        p_mh.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        
        r_num = p_mh.add_run(f"{item['num']}. {item['name'].upper()} ")
        r_num.font.name = "Segoe UI"
        r_num.font.size = Pt(11)
        r_num.font.bold = True
        r_num.font.color.rgb = NAVY

        # Assigned Topic
        p_top = cell.add_paragraph()
        p_top.paragraph_format.space_before = Pt(2)
        p_top.paragraph_format.space_after = Pt(2)
        p_top.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        
        r_tl = p_top.add_run("Assigned Topic: ")
        r_tl.font.name = "Segoe UI"
        r_tl.font.size = Pt(9.5)
        r_tl.font.bold = True
        r_tl.font.color.rgb = ACCENT_BLUE

        r_tv = p_top.add_run(item['topic'])
        r_tv.font.name = "Segoe UI"
        r_tv.font.size = Pt(9.5)
        r_tv.font.bold = True
        r_tv.font.color.rgb = CHARCOAL

        # Relevant Paper Sections
        p_sec = cell.add_paragraph()
        p_sec.paragraph_format.space_before = Pt(1)
        p_sec.paragraph_format.space_after = Pt(4)
        p_sec.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        
        r_sl = p_sec.add_run("Paper Sections: ")
        r_sl.font.name = "Segoe UI"
        r_sl.font.size = Pt(8.5)
        r_sl.font.bold = True
        r_sl.font.color.rgb = DARK_GRAY

        r_sv = p_sec.add_run(item['sections'])
        r_sv.font.name = "Segoe UI"
        r_sv.font.size = Pt(8.5)
        r_sv.font.italic = True
        r_sv.font.color.rgb = DARK_GRAY

        # Research Scope / Bullet points
        for pt in item['scope']:
            p_pt = cell.add_paragraph()
            p_pt.paragraph_format.space_before = Pt(1)
            p_pt.paragraph_format.space_after = Pt(2)
            p_pt.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            p_pt.paragraph_format.left_indent = Inches(0.2)
            
            r_b = p_pt.add_run("• ")
            r_b.font.name = "Segoe UI"
            r_b.font.size = Pt(8.5)
            r_b.font.bold = True
            r_b.font.color.rgb = ACCENT_BLUE

            r_txt = p_pt.add_run(pt)
            r_txt.font.name = "Segoe UI"
            r_txt.font.size = Pt(8.5)
            r_txt.font.color.rgb = CHARCOAL

        # Spacing after card
        p_sp = doc.add_paragraph()
        p_sp.paragraph_format.space_before = Pt(0)
        p_sp.paragraph_format.space_after = Pt(4)
        p_sp.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

    doc.save(DOCX_PATH)
    print(f"Task Allocation DOCX created at {DOCX_PATH}")

if __name__ == "__main__":
    build_allocation_doc()
