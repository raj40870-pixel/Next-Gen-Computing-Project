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

# 1. Overview Map (scrolled slightly to center map)
driver.execute_script("document.querySelector('section[data-testid=\"stMain\"]').scrollTop = 180;")
time.sleep(2)
driver.save_screenshot(os.path.join(out_dir, 'real_prototype_map.png'))
print('[+] 1. Saved real_prototype_map.png')

# 2. 30-Day Forecast - scroll to graphs
radios = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stRadio'] label")
for r in radios:
    if '30-Day Forecast' in r.text:
        r.click()
        time.sleep(4)
        driver.execute_script("document.querySelector('section[data-testid=\"stMain\"]').scrollTop = 700;")
        time.sleep(2.5)
        driver.save_screenshot(os.path.join(out_dir, 'real_prototype_forecast_graph.png'))
        print('[+] 2. Saved real_prototype_forecast_graph.png')
        break

# 3. What-If Simulator - scroll to sliders and bars
radios = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stRadio'] label")
for r in radios:
    if 'What-If Climate' in r.text:
        r.click()
        time.sleep(4)
        driver.execute_script("document.querySelector('section[data-testid=\"stMain\"]').scrollTop = 260;")
        time.sleep(2.5)
        driver.save_screenshot(os.path.join(out_dir, 'real_prototype_simulator.png'))
        print('[+] 3. Saved real_prototype_simulator.png')
        break

# 4. Live Satellite Sync Hub - scroll to table
radios = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stRadio'] label")
for r in radios:
    if 'Live Satellite Sync' in r.text:
        r.click()
        time.sleep(4)
        driver.execute_script("document.querySelector('section[data-testid=\"stMain\"]').scrollTop = 480;")
        time.sleep(2.5)
        driver.save_screenshot(os.path.join(out_dir, 'real_prototype_telemetry_table.png'))
        print('[+] 4. Saved real_prototype_telemetry_table.png')
        break

# 5. Model Benchmarking Lab - scroll to comparisons
radios = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stRadio'] label")
for r in radios:
    if 'Model Benchmarking' in r.text:
        r.click()
        time.sleep(4)
        driver.execute_script("document.querySelector('section[data-testid=\"stMain\"]').scrollTop = 220;")
        time.sleep(2.5)
        driver.save_screenshot(os.path.join(out_dir, 'real_prototype_benchmarking.png'))
        print('[+] 5. Saved real_prototype_benchmarking.png')
        break

driver.quit()
print('\n[+] ALL REAL PROTOTYPE SCREENSHOTS CAPTURED PERFECTLY!')
