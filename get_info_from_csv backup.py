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
BASE_FOLDER = "images"
CSV_FILENAME = "download_result.csv"
RECORD_ID_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "record_ids.csv")

# Chrome起動
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# ログイン
def login():
    driver.get("https://rukitech.cybozu.com/login")
    time.sleep(2)
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.CLASS_NAME, "login-button").click()
    time.sleep(5)

# ブロック画像保存
def download_images_from_block(session, headers, base_path, class_name, label):
    try:
        block = driver.find_element(By.CLASS_NAME, class_name)
        imgs = block.find_elements(By.TAG_NAME, "img")
        if not imgs:
            print(f"⚠️ {label}：画像がないためフォルダーを作成しません")
            return
        for idx, img in enumerate(imgs):
            src = img.get_attribute("src")
            if src and "download.do" in src:
                response = session.get(src, headers=headers)
                if response.status_code == 200:
                    folder = os.path.join(base_path, label)
                    os.makedirs(folder, exist_ok=True)
                    filename = f"{label}_{idx}.jpg"
                    with open(os.path.join(folder, filename), "wb") as f:
                        f.write(response.content)
    except:
        print(f"⚠️ {label} ブロックなし → スキップ")

# レコード詳細取得・保存
def scrape_images_and_save_csv(record_number):
    TARGET_URL = f"https://rukitech.cybozu.com/k/3/show#record={record_number}"
    driver.get(TARGET_URL)
    time.sleep(5)

    cookies = driver.get_cookies()
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])
    headers = {"User-Agent": "Mozilla/5.0"}

    def safe_text(cls):
        try:
            return driver.find_element(By.CLASS_NAME, cls).text.strip()
        except:
            return ""

    control_number = safe_text("value-5520009")
    control_date_of_reception = safe_text("value-5519916") or time.strftime("%Y-%m-%d")

    base_name = control_number if control_number else control_date_of_reception.replace('/', '-')
    folder_name = base_name
    suffix = 1
    while os.path.exists(os.path.join(BASE_FOLDER, folder_name)):
        folder_name = f"{base_name}({suffix})"
        suffix += 1

    record_folder = os.path.join(BASE_FOLDER, folder_name)
    os.makedirs(record_folder, exist_ok=True)

    row_data = [
        control_number, safe_text("value-5519959"), control_date_of_reception, safe_text("value-5519990"),
        safe_text("value-5520007"), safe_text("value-5519998"), safe_text("value-5519950"), safe_text("value-5519951"),
        safe_text("value-5520005"), safe_text("value-5519954"), safe_text("value-5118243"), safe_text("value-5118231"),
        safe_text("value-5118233"), safe_text("value-5519917"), safe_text("value-5519930")
    ]

    headers_row = [
        'Control Number', 'Name', 'Date of Reception', 'Expiry Date', 'Completion Date',
        'Contact', 'Status', 'Initial Analysis', 'Payment Confirmation', 'Operator',
        'Manufacturer', 'Registered By', 'Registration Date', 'Condition Details', 'Remarks'
    ]

    with open(CSV_FILENAME, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if os.stat(CSV_FILENAME).st_size == 0:
            writer.writerow(headers_row)
        writer.writerow(row_data)

    indiv_csv = os.path.join(record_folder, f"{folder_name}.csv")
    write_header = not os.path.exists(indiv_csv)
    with open(indiv_csv, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(headers_row)
        writer.writerow(row_data)

    download_images_from_block(session, headers, record_folder, "value-5519927", "作業中")
    download_images_from_block(session, headers, record_folder, "value-5519928", "パーツナンバーや故障箇所")

    all_imgs = driver.find_elements(By.CSS_SELECTOR, ".value-5519926 img")
    if all_imgs:
        folder = os.path.join(record_folder, "登録時・割れや傷")
        os.makedirs(folder, exist_ok=True)
        for idx, img in enumerate(all_imgs):
            src = img.get_attribute("src")
            if src and "download.do" in src:
                try:
                    res = session.get(src, headers=headers)
                    if res.status_code == 200:
                        filename = f"登録時・割れや傷_{idx}.jpg"
                        with open(os.path.join(folder, filename), "wb") as f:
                            f.write(res.content)
                except Exception as e:
                    print(f"❌ 登録時画像のダウンロード失敗: {e}")
    else:
        print("⚠️ 登録時・割れや傷：画像がないためフォルダーを作成しません")

# 実行ブロック（CSVからID読み込み）
if __name__ == "__main__":
    login()

    record_ids = []
    try:
        with open(RECORD_ID_CSV, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # ヘッダーをスキップ
            for row in reader:
                if row and row[0].isdigit():
                    record_ids.append(int(row[0]))
    except Exception as e:
        print(f"❌ record_ids.csv の読み込みエラー: {e}")
        driver.quit()
        exit(1)

    for rid in record_ids:
        try:
            print(f"\n--- Record {rid} 処理中 ---")
            scrape_images_and_save_csv(rid)
        except Exception as e:
            print(f"❌ Record {rid} エラー: {e}")

    driver.quit()
    print("\n🎉 全て完了しました！（CSVからID使用）")
