from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
import requests
import csv
import re

# 設定
USERNAME = "info@rukitech.net"
PASSWORD = "Rukitech1360"
LOGIN_URL = "https://rukitech.cybozu.com/login"
LIST_URL = "https://rukitech.cybozu.com/k/3/"
BASE_FOLDER = "images"
CSV_FILENAME = "download_result.csv"
RECORD_ID_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "record_ids.csv")

# Chrome起動
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# ログイン
def login():
    driver.get(LOGIN_URL)
    time.sleep(2)
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.CLASS_NAME, "login-button").click()
    time.sleep(5)

# レコード一覧取得
def get_record_ids_from_list():
    driver.get(LIST_URL)
    time.sleep(5)
    all_record_ids = set()

    while True:
        print("📄 レコード一覧ページ取得中...")
        links = driver.find_elements(By.TAG_NAME, "a")
        hrefs = []
        for link in links:
            try:
                href = link.get_attribute("href")
                if href:
                    hrefs.append(href)
            except Exception as e:
                print(f"⚠️ スキップされたリンク: {e}")

        for href in hrefs:
            if "show#record=" in href:
                match = re.search(r"record=(\d+)", href)
                if match:
                    record_id = int(match.group(1))
                    all_record_ids.add(record_id)
                    print(f"✅ 見つかったレコードID: {record_id}")

        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, '.gaia-ui-listtable-pagercomponent-next')
            next_class = next_btn.get_attribute('class')
            if 'pager-disable' in next_class:
                print("✅ 最後のページです")
                break
            print("➡️ 次のページへ移動します")
            next_btn.click()
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ 次ページ移動失敗: {e}")
            break

    sorted_ids = sorted(all_record_ids)
    print(f"📝 {len(sorted_ids)} 件のIDをCSVに保存します → {RECORD_ID_CSV}")

    try:
        with open(RECORD_ID_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Record ID"])
            for rid in sorted_ids:
                writer.writerow([rid])
        print("✅ CSV書き出し完了")
    except Exception as e:
        print(f"❌ CSV書き出し失敗: {e}")

    return sorted_ids