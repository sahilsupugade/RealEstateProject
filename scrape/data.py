from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import numpy as np
import os
import random
import pandas as pd

# Load existing data to skip already scraped links
df = pd.read_csv('combined_data.csv')
links_fetched = set(df['link'])

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
    'Mozilla/5.0 (X11; Linux x86_64)...'
]

def create_driver(user_agent):
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument(f"--window-size={random.randint(1200,1600)},{random.randint(800,1000)}")
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd(
        'Page.addScriptToEvaluateOnNewDocument',
        {'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'}
    )
    return driver

def click_next_page(driver, wait, max_scrolls=25):
    for scroll_count in range(max_scrolls):
        try:
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Next Page")]')))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            time.sleep(1)
            try:
                next_button.click()
                print("✅ Clicked 'Next Page' using normal click.")
            except:
                driver.execute_script("arguments[0].click();", next_button)
                print("✅ Clicked 'Next Page' using JavaScript click.")
            return True
        except:
            driver.execute_script("window.scrollBy(0, 3000);")
            print(f"🔃 Scrolling... (attempt {scroll_count + 1})")
            time.sleep(1)
    print("❌ Failed to find/click 'Next Page'.")
    return False

# Setup
os.makedirs("data_resales", exist_ok=True)
visited_links = set()
flat = 6308
skip = 0
i = 100

current_user_agent = random.choice(USER_AGENTS)
driver = create_driver(current_user_agent)
wait = WebDriverWait(driver, 10)
driver.get(f'https://www.99acres.com/flats-in-mumbai-ffid{i}')
start_time = time.time()

while True:
    try:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "tupleNew__outerTupleWrap")))
    except Exception as e:
        print(f"⚠️ Error on page {i}: {e}")
        continue

    containers = driver.find_elements(By.CLASS_NAME, "tupleNew__outerTupleWrap")
    if not containers:
        print(f"⚠ No containers found on page {i}. Trying to reload...")
        time.sleep(2)
        continue

    print(f"📦 Found {len(containers)} containers on page {i}")
    for idx, elem in enumerate(containers):
        try:
            html_content = elem.get_attribute("outerHTML")
            link_elem = elem.find_element(By.CSS_SELECTOR, "a.tupleNew__propertyHeading.ellipsis")
            link = link_elem.get_attribute("href")
            if link and not link.startswith('http'):
                link = "https://www.99acres.com" + link

            if link and link not in visited_links and link not in links_fetched:
                visited_links.add(link)
                file_path = f"data_flats/flat_{flat}.html"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"✅ Container saved: {link}")
                flat += 1
            else:
                skip += 1
                print(f"⏩ Skipping duplicate ({skip}): {link}")

            time.sleep(np.random.uniform(1, 3))
        except Exception as e:
            print(f"❌ Error extracting container index {idx}: {e}")
            continue

    # Move to next page
    if not click_next_page(driver, wait):
        break

    i += 1
    if i % 3 == 0:
        sleep_time = random.uniform(10, 15)
        print(f"🛑 Short break after {i} pages: sleeping for {sleep_time:.1f} sec")
        time.sleep(sleep_time)

driver.quit()
end_time = time.time()
print(f"⏱ Total scrape time: {(end_time - start_time)/60:.2f} minutes")
