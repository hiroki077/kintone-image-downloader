from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
import csv
import re

# ——— 設定 ———
USERNAME = input("ユーザー名を入力してください: ")
PASSWORD = input("パスワードを入力してください: ")
domain = input("ログインURL（例 https://example.cybozu.com ）を入力してください: ").rstrip("/")
app_number = input("アプリケーションナンバーを入力してください: ")

LOGIN_URL = f"{domain}/login"
LIST_URL = f"{domain}/k/{app_number}/"

# 保存先設定
BASE_FOLDER = "images"
os.makedirs(BASE_FOLDER, exist_ok=True)
RECORD_ID_CSV = os.path.join(BASE_FOLDER, "record_ids.csv")

# Chrome 起動オプション
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# ——— ログイン関数 ———
def login():
    driver.get(LOGIN_URL)
    time.sleep(2)
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
    time.sleep(5)

# ——— レコード一覧から ID を取得して CSV に保存 ———
def get_record_ids_from_list():
    driver.get(LIST_URL)
    time.sleep(5)
    record_ids = set()

    while True:
        print("📄 レコード一覧ページ取得中...")
        for elem in driver.find_elements(By.TAG_NAME, "a"):
            href = elem.get_attribute("href") or ""
            m = re.search(r"show#record=(\d+)", href)
            if m:
                rid = int(m.group(1))
                if rid not in record_ids:
                    record_ids.add(rid)
                    print(f"✅ 見つかったレコードID: {rid}")

        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, ".gaia-ui-listtable-pagercomponent-next")
            if "pager-disable" in next_btn.get_attribute("class"):
                print("✅ 最後のページです")
                break
            print("➡️ 次のページへ移動します")
            next_btn.click()
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ 次ページ移動失敗またはボタン未検出: {e}")
            break

    sorted_ids = sorted(record_ids)
    print(f"📝 {len(sorted_ids)} 件のIDを CSV に保存します → {RECORD_ID_CSV}")

    try:
        with open(RECORD_ID_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Record ID"])
            for rid in sorted_ids:
                writer.writerow([rid])
        print("✅ CSV 書き出し完了")
    except Exception as e:
        print(f"❌ CSV 書き出し失敗: {e}")

    return sorted_ids

if __name__ == "__main__":
    login()
    ids = get_record_ids_from_list()
    print("取得したレコードID一覧:", ids)
    driver.quit()
