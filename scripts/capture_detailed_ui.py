import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_argument('--headless=new')
options.add_argument('--window-size=1550,1100')

driver = webdriver.Chrome(options=options)
driver.get('http://localhost:8501')
time.sleep(5)

out_dir = os.path.join('data', 'patent_figures')
os.makedirs(out_dir, exist_ok=True)

# 1. Main Overview & Map
driver.save_screenshot(os.path.join(out_dir, 'real_ui_overview.png'))
print('[+] 1. Saved real_ui_overview.png')

# 2. Tab 2: 30-Day Forecast Explorer - Scrolled to show graphs
radios = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stRadio'] label")
for r in radios:
    if '30-Day Forecast' in r.text:
        r.click()
        time.sleep(4)
        # Scroll down slightly to show the forecast plot clearly
        driver.execute_script("window.scrollTo(0, 420);")
        time.sleep(1.5)
        driver.save_screenshot(os.path.join(out_dir, 'real_ui_forecast_graph.png'))
        print('[+] 2. Saved real_ui_forecast_graph.png')
        break

# 3. Tab 0: Live Satellite Sync Hub
radios = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stRadio'] label")
for r in radios:
    if 'Live Satellite Sync' in r.text:
        r.click()
        time.sleep(4)
        driver.execute_script("window.scrollTo(0, 350);")
        time.sleep(1.5)
        driver.save_screenshot(os.path.join(out_dir, 'real_ui_satellite_telemetry.png'))
        print('[+] 3. Saved real_ui_satellite_telemetry.png')
        break

# 4. Tab 3: What-If Climate Scenario Simulator
radios = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stRadio'] label")
for r in radios:
    if 'What-If Climate' in r.text:
        r.click()
        time.sleep(4)
        driver.execute_script("window.scrollTo(0, 200);")
        time.sleep(1.5)
        driver.save_screenshot(os.path.join(out_dir, 'real_ui_scenario_simulator.png'))
        print('[+] 4. Saved real_ui_scenario_simulator.png')
        break

# 5. Tab 4: Model Benchmarking Lab
radios = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stRadio'] label")
for r in radios:
    if 'Model Benchmarking' in r.text:
        r.click()
        time.sleep(4)
        driver.execute_script("window.scrollTo(0, 180);")
        time.sleep(1.5)
        driver.save_screenshot(os.path.join(out_dir, 'real_ui_benchmarking_lab.png'))
        print('[+] 5. Saved real_ui_benchmarking_lab.png')
        break

driver.quit()
print('\n[+] All high-detail real Streamlit UI screenshots captured successfully!')
