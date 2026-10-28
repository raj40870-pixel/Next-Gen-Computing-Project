import os
import sys
import subprocess
import pypdf

# Let's define parameter combinations to find exactly 10 pages
configs = [
    (9.4, 1.14, 4.2),
    (9.6, 1.15, 4.5),
    (9.8, 1.16, 5.0),
    (9.2, 1.12, 3.8),
]

for font_pt, line_sp, space_after in configs:
    print(f"\n--- Testing font_pt={font_pt}, line_sp={line_sp}, space_after={space_after} ---")
    cmd_docx = f"python scripts/generate_hindi_research_paper.py {font_pt} {line_sp} {space_after}"
    res = subprocess.run(cmd_docx, shell=True, capture_output=True, text=True)
    print("DOCX gen output:", res.stdout.strip())
    
    cmd_pdf = "powershell -ExecutionPolicy Bypass -File scripts/convert_hindi_pdf.ps1"
    res_pdf = subprocess.run(cmd_pdf, shell=True, capture_output=True, text=True)
    
    pdf_path = r"C:\Users\Kamaljit\Downloads\Groundwater_STGNN_Research_Paper_HINDI.pdf"
    if os.path.exists(pdf_path):
        reader = pypdf.PdfReader(pdf_path)
        pages = len(reader.pages)
        print(f"RESULT: Page Count = {pages}")
        if pages == 10:
            print(f"SUCCESS! Exactly 10 pages achieved with font_pt={font_pt}, line_sp={line_sp}, space_after={space_after}")
            break
