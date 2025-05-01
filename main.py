from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import requests
import csv
import re

# ── 設定 ─────────────────────────────────────────
USERNAME       = input("ユーザー名を入力してください: ")
PASSWORD       = input("パスワードを入力してください: ")
domain         = input("ログインURL(使用ドメイン、例 https://example.cybozu.com) を入力してください: ").rstrip("/")
LOGIN_URL      = f"{domain}/login"

app_number     = input("アプリケーションナンバーを入力してください: ")
LIST_URL       = f"{domain}/k/{app_number}/"     # レコード一覧画面
APP_URL_TMPL   = f"{domain}/k/{app_number}/show#record={{}}"

BASE_FOLDER    = "images"
CSV_FILENAME   = "download_result.csv"
RECORD_ID_CSV  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "record_ids.csv")

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

def get_record_ids_from_list():
    """
    アプリの一覧画面からすべてのページを巡回して
    レコードIDを収集し、record_ids.csv に保存する
    """
    driver.get(LIST_URL)
    time.sleep(5)
    all_record_ids = set()

    while True:
        print("📄 レコード一覧ページ取得中...")
        # 全リンクから record= を抽出
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href") or ""
            if "show#record=" in href:
                m = re.search(r"record=(\d+)", href)
                if m:
                    rid = int(m.group(1))
                    if rid not in all_record_ids:
                        all_record_ids.add(rid)
                        print(f"✅ 見つかったレコードID: {rid}")

        # ページネーション「次へ」ボタン
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, ".gaia-ui-listtable-pagercomponent-next")
            if "pager-disable" in next_btn.get_attribute("class"):
                print("✅ 最後のページです")
                break
            print("➡️ 次のページへ移動します")
            next_btn.click()
            time.sleep(3)
        except:
            print("⚠️ 次ページ移動できませんでした")
            break

    sorted_ids = sorted(all_record_ids)
    # CSV に保存
    with open(RECORD_ID_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Record ID"])
        for rid in sorted_ids:
            writer.writerow([rid])
    print(f"📝 {len(sorted_ids)} 件のIDを {RECORD_ID_CSV} に保存しました")
    return sorted_ids

def download_slideshow_images(session, headers, record_folder, class_name, label, downloaded_urls):
    """
    サムネイルをJSクリック→モーダル中の高画質スライドをDL→ESC で閉じる
    """
    try:
        block = driver.find_element(By.CLASS_NAME, class_name)
        thumbs = block.find_elements(By.TAG_NAME, "img")
        if not thumbs:
            print(f"⚠️ {label}：サムネイルが見つかりません")
            return
        folder = os.path.join(record_folder, label)
        os.makedirs(folder, exist_ok=True)

        for idx, thumb in enumerate(thumbs):
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", thumb)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", thumb)

            slide = wait.until(EC.visibility_of_element_located((
                By.CSS_SELECTOR, ".slide-image-cybozu.slide-current img"
            )))
            src = slide.get_attribute("src")
            if src and src not in downloaded_urls:
                r = session.get(src, headers=headers)
                if r.status_code == 200:
                    fn = f"{label}_hq_{idx}.jpg"
                    with open(os.path.join(folder, fn), "wb") as f:
                        f.write(r.content)
                    downloaded_urls.add(src)
                    print(f"✅ {label} DL: {fn}")
                else:
                    print(f"❌ {label} DL失敗 HTTP {r.status_code}")

            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.3)

    except Exception as e:
        print(f"⚠️ {label} のDLエラー: {e}")

def scrape_images_and_save_csv(record_number):
    # レコード詳細画面を開く
    driver.get(APP_URL_TMPL.format(record_number))
    time.sleep(5)

    # セッション構築 (cookies→requests)
    session = requests.Session()
    for c in driver.get_cookies():
        session.cookies.set(c['name'], c['value'])
    headers = {"User-Agent": "Mozilla/5.0"}

    # テキスト情報取得＆フォルダ設定
    ctrl_no = safe_text("value-5520009")
    recv_dt = safe_text("value-5519916") or time.strftime("%Y-%m-%d")
    base    = ctrl_no or recv_dt.replace("/", "-")
    name    = base
    c       = 1
    while os.path.exists(os.path.join(BASE_FOLDER, name)):
        name = f"{base}({c})"
        c += 1
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
        w = csv.writer(f)
        if os.stat(CSV_FILENAME).st_size == 0:
            w.writerow(cols)
        w.writerow(row)
    indiv_csv = os.path.join(record_folder, f"{name}.csv")
    need_header = not os.path.exists(indiv_csv)
    with open(indiv_csv, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if need_header:
            w.writerow(cols)
        w.writerow(row)

    # 高画質ダウンロード用セット
    downloaded_urls = set()

    # 各ファイルフィールドをスライド経由でDL
    download_slideshow_images(session, headers, record_folder, "value-5519927", "作業中", downloaded_urls)
    download_slideshow_images(session, headers, record_folder, "value-5519928", "パーツナンバーや故障箇所", downloaded_urls)
    download_slideshow_images(session, headers, record_folder, "value-5519926", "登録時・割れや傷", downloaded_urls)

if __name__ == "__main__":
    login()

    # レコード一覧からIDを取得
    record_ids = get_record_ids_from_list()

    # 各レコードを処理
    for rid in record_ids:
        print(f"\n--- Record {rid} 処理中 ---")
        try:
            scrape_images_and_save_csv(rid)
        except Exception as e:
            print(f"❌ Record {rid} エラー: {e}")

    driver.quit()
    print("\n🎉 全て完了しました！")
