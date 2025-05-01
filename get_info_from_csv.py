from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import requests
import csv

# ── 設定 ─────────────────────────────────────────
USERNAME = input("ユーザー名を入力してください: ")
PASSWORD = input("パスワードを入力してください: ")
domain = input("ログインURL(使用ドメイン、例 https://example.cybozu.com) を入力してください: ").rstrip("/")
LOGIN_URL = f"{domain}/login"

app_number = input("アプリケーションナンバーを入力してください: ")
APP_URL_TMPL = f"{domain}/k/{app_number}/show#record={{}}"

BASE_FOLDER   = "images"
CSV_FILENAME  = "download_result.csv"
RECORD_ID_CSV = os.path.join(os.path.dirname(__file__), "record_ids.csv")

# ── Chrome ドライバ起動 & 待機オブジェクト ─────────────────
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

def login():
    driver.get(LOGIN_URL)
    time.sleep(2)
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.CLASS_NAME, "login-button").click()
    time.sleep(5)

def safe_text(class_name):
    try:
        return driver.find_element(By.CLASS_NAME, class_name).text.strip()
    except:
        return ""

def download_slideshow_images(session, headers, record_folder, class_name, label, downloaded_urls):
    """
    サムネイルをJSクリック→モーダル(.slide-current)内imgを高画質DL→ESCで閉じ
    """
    try:
        block = driver.find_element(By.CLASS_NAME, class_name)
        thumbs = block.find_elements(By.TAG_NAME, "img")
        if not thumbs:
            print(f"⚠️ {label}：サムネイルなし")
            return
        folder = os.path.join(record_folder, label)
        os.makedirs(folder, exist_ok=True)

        for idx, thumb in enumerate(thumbs):
            # 画面中央にスクロール→JSクリック
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", thumb)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", thumb)

            # 高解像度画像の出現待ち
            slide = wait.until(EC.visibility_of_element_located((
                By.CSS_SELECTOR, ".slide-image-cybozu.slide-current img"
            )))
            src = slide.get_attribute("src")
            # 未取得かつURLがある場合のみDL
            if src and src not in downloaded_urls:
                r = session.get(src, headers=headers)
                if r.status_code == 200:
                    fn = f"{label}_hq_{idx}.jpg"
                    with open(os.path.join(folder, fn), "wb") as f:
                        f.write(r.content)
                    downloaded_urls.add(src)
                    print(f"✅ スライドDL: {label}/{fn}")
                else:
                    print(f"❌ スライドDL失敗 HTTP {r.status_code}")
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.3)

    except Exception as e:
        print(f"⚠️ {label} のスライドDL中にエラー: {e}")

def scrape_images_and_save_csv(record_number):
    driver.get(APP_URL_TMPL.format(record_number))
    time.sleep(5)

    # セッション構築（cookies → requests）
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])
    headers = {"User-Agent": "Mozilla/5.0"}

    # テキスト取得 & フォルダ準備
    ctrl_no = safe_text("value-5520009")
    recv_dt = safe_text("value-5519916") or time.strftime("%Y-%m-%d")
    base    = ctrl_no or recv_dt.replace("/", "-")
    name    = base
    cnt     = 1
    while os.path.exists(os.path.join(BASE_FOLDER, name)):
        name = f"{base}({cnt})"
        cnt += 1
    record_folder = os.path.join(BASE_FOLDER, name)
    os.makedirs(record_folder, exist_ok=True)

    # CSV 書き出し
    row = [
        ctrl_no, safe_text("value-5519959"), recv_dt, safe_text("value-5519990"),
        safe_text("value-5520007"), safe_text("value-5519998"), safe_text("value-5519950"),
        safe_text("value-5519951"), safe_text("value-5520005"), safe_text("value-5519954"),
        safe_text("value-5118243"), safe_text("value-5118231"), safe_text("value-5118233"),
        safe_text("value-5519917"), safe_text("value-5519930")
    ]
    cols = [
        'Control Number','Name','Date of Reception','Expiry Date','Completion Date',
        'Contact','Status','Initial Analysis','Payment Confirmation','Operator',
        'Manufacturer','Registered By','Registration Date','Condition Details','Remarks'
    ]
    with open(CSV_FILENAME, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if os.stat(CSV_FILENAME).st_size == 0:
            writer.writerow(cols)
        writer.writerow(row)
    indiv_csv = os.path.join(record_folder, f"{name}.csv")
    need_header = not os.path.exists(indiv_csv)
    with open(indiv_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if need_header:
            writer.writerow(cols)
        writer.writerow(row)

    # URL 重複防止セット
    downloaded_urls = set()

    # 各フィールドをスライド経由で高画質取得
    download_slideshow_images(session, headers, record_folder, "value-5519927", "作業中", downloaded_urls)
    download_slideshow_images(session, headers, record_folder, "value-5519928", "パーツナンバーや故障箇所", downloaded_urls)
    download_slideshow_images(session, headers, record_folder, "value-5519926", "登録時・割れや傷", downloaded_urls)

if __name__ == "__main__":
    login()
    # record_ids.csv から対象レコードIDを取得
    record_ids = []
    try:
        with open(RECORD_ID_CSV, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row and row[0].isdigit():
                    record_ids.append(int(row[0]))
    except Exception as e:
        print(f"❌ record_ids.csv 読み込みエラー: {e}")
        driver.quit()
        exit(1)

    # 各レコードを処理
    for rid in record_ids:
        print(f"\n--- Record {rid} 処理中 ---")
        try:
            scrape_images_and_save_csv(rid)
        except Exception as e:
            print(f"❌ Record {rid} エラー: {e}")

    driver.quit()
    print("\n全て完了しました！")
