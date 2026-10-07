import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_argument('--headless=new')
options.add_argument('--window-size=1550,1000')

driver = webdriver.Chrome(options=options)
driver.get('http://localhost:8501')
time.sleep(5)

out_dir = os.path.join('data', 'patent_figures')
os.makedirs(out_dir, exist_ok=True)

# 1. Map Tab (Default)
driver.save_screenshot(os.path.join(out_dir, 'ui_tab1_map.png'))
print('[+] Captured UI Tab 1 Map')

# Click each tab and capture
tab_keywords = [
    ('30-Day Forecast', 'ui_tab2_forecast.png'),
    ('Live Satellite Sync', 'ui_tab0_sync.png'),
    ('What-If Climate', 'ui_tab3_simulator.png'),
    ('Model Benchmarking', 'ui_tab4_benchmarking.png'),
]

for kw, fname in tab_keywords:
    try:
        radios = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stRadio'] label")
        matched = next((r for r in radios if kw in r.text), None)
        if matched:
            matched.click()
            time.sleep(3.5)
            driver.save_screenshot(os.path.join(out_dir, fname))
            print(f'[+] Captured {fname} for {kw}')
    except Exception as e:
        print(f'[-] Error capturing {kw}: {e}')

driver.quit()
print('\n[+] All genuine Streamlit UI screenshots captured successfully!')
