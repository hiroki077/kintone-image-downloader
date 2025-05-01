# kintone-image-downloader

A Selenium + Python script to batch-download high-resolution images from Kintone records and export associated text data to CSV.

## Usage

1. **Run `main.py`**  
   - The script will automatically:
     1. Navigate to the Kintone record list view and collect all record IDs into `record_ids.csv`.  
     2. Visit each record’s detail page, download high-resolution images for each file field, and save them under `images/<Record_ID>/`.  
     3. Extract key text fields (control number, name, reception date, etc.) and append them to `download_result.csv`.

2. **Enter the required information when prompted**:  
   - **Username**  
   - **Password**  
   - **Kintone domain URL** (e.g. `https://example.cybozu.com`)  
   - **Application number** (the `/k/<app_number>/` part of your Kintone URL)

3. **Check the output**:  
   - `record_ids.csv` — list of all record IDs  
   - `images/` — subfolders per record containing high-res images  
   - `download_result.csv` — aggregated text fields for all records

## Prerequisites

- **Python 3.8+**  
- **Google Chrome** + matching **ChromeDriver** installed and on `PATH`  
- Internet access to your Kintone instance  
- Install dependencies:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate    # macOS / Linux
  .venv\Scripts\activate       # Windows
  pip install -r requirements.txt



Kintone レコードの画像を高画質でまとめてダウンロードする Selenium + Python スクリプトです。

## 使い方

1. **main.py** を実行すると、  
   - レコード一覧画面を巡回してすべてのレコードIDを `record_ids.csv` に書き出し  
   - 各レコード詳細画面に遷移して高画質画像をダウンロード  
   - テキスト情報を `download_result.csv` にまとめて出力  
   という一連の処理がまとめて完結します。

2. プロンプトに従って以下の情報を入力します：  
   - Kintone の **ユーザー名**  
   - Kintone の **パスワード**  
   - Kintone の **ドメイン URL**（例: `https://example.cybozu.com`）  
   - **アプリケーション番号**（URL の `/k/アプリ番号/` 部分）

3. スクリプト実行中に自動的に  
   - `record_ids.csv`（レコードID一覧）  
   - `images/` フォルダ（レコードごとにサブフォルダを作成、高画質画像を格納）  
   - `download_result.csv`（各レコードのテキスト情報）  
   が出力されます。

4. 処理が完了したら、  
   - `images/` 以下の各フォルダ内をご確認ください  
   - `download_result.csv` を開けば管理番号・受付日・氏名などを一覧できます  

## 前提条件

- Python 3.8 以上  
- Google Chrome と対応する **ChromeDriver** がインストールされ、実行環境の PATH に含まれていること  
- ネットワークから Kintone へアクセス可能であること  
- `requirements.txt` に記載のパッケージをインストール済みであること  

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows

pip install -r requirements.txt
