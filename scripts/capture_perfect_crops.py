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

# 1. Main Overview UI
driver.save_screenshot(os.path.join(out_dir, 'real_ui_overview.png'))

# 2. 30-Day Forecast Explorer - scroll right to the curve
radios = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stRadio'] label")
for r in radios:
    if '30-Day Forecast' in r.text:
        r.click()
        time.sleep(4)
        driver.execute_script("window.scrollTo(0, 680);")
        time.sleep(2)
        driver.save_screenshot(os.path.join(out_dir, 'real_ui_forecast_curve.png'))
        break

# 3. What-If Simulator - scroll to show sliders and bars
radios = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stRadio'] label")
for r in radios:
    if 'What-If Climate' in r.text:
        r.click()
        time.sleep(4)
        driver.execute_script("window.scrollTo(0, 380);")
        time.sleep(2)
        driver.save_screenshot(os.path.join(out_dir, 'real_ui_simulator_bars.png'))
        break

# 4. Live Satellite Sync Hub - scroll to show real-time telemetry table
radios = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stRadio'] label")
for r in radios:
    if 'Live Satellite Sync' in r.text:
        r.click()
        time.sleep(4)
        driver.execute_script("window.scrollTo(0, 480);")
        time.sleep(2)
        driver.save_screenshot(os.path.join(out_dir, 'real_ui_telemetry_table.png'))
        break

# 5. Model Benchmarking Lab - scroll to show model comparison charts
radios = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stRadio'] label")
for r in radios:
    if 'Model Benchmarking' in r.text:
        r.click()
        time.sleep(4)
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(2)
        driver.save_screenshot(os.path.join(out_dir, 'real_ui_benchmarking_charts.png'))
        break

driver.quit()
print('\n[+] Captured perfectly scrolled views of all Streamlit prototype components!')
