# WiWA CMS

No magic. Just code.()
One path. One route. One truth.

Pythonが書ければ、そのまま運用・拡張できるCMSです。
A CMS you can run and extend as-is, if you can write Python.

---

## 要件 / Requirements

### 対応環境 / Environment

* Ubuntu 24.04（推奨）
  Ubuntu 24.04 (recommended)

* Python 3.12 以上
  Python 3.12+

---

## セットアップ / Setup

### 必須パッケージ / Required packages

sudo apt update
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    libmagic1

---

### 推奨パッケージ / Recommended packages

sudo apt install -y \
    nginx \
    git

---

## MongoDB のインストール / Install MongoDB

WiWAはMongoDBを使用します。
WiWA uses MongoDB.

### リポジトリ追加 / Add repository

curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
    sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

echo "deb [signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg] \
https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/7.0 multiverse" | \
    sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

---

### インストール / Install

sudo apt update
sudo apt install -y mongodb-org

---

### 起動 / Start

sudo systemctl start mongod
sudo systemctl enable mongod

---

### 確認 / Verify

mongosh

---

## プロジェクトセットアップ / Project setup

### クローン / Clone

git clone https://github.com/your-repo/wiwa.git
cd wiwa

---

### 仮想環境 / Virtual environment

python3 -m venv venv
source venv/bin/activate

---

### Pythonパッケージ / Python packages

pip install -r requirements.txt

---

## 起動 / Run

python run.py

---

## アクセス / Access

http://127.0.0.1:8000

---

## 管理機能 / Admin

/admin
/mypage

---

## ファイルアップロード / File upload

* admin / author のみアップロード可能  
  Only admin / author can upload

* 対応形式 / Allowed MIME types

image/apng  
image/avif  
image/gif  
image/jpeg  
image/png  
image/tiff  
image/webp  
application/pdf

* 保存先 / Storage

/uploads/image/  
/uploads/file/

---

## Nginx 設定 / Nginx configuration

WiWAでは静的ファイルはnginxで配信します。  
WiWA serves static files via nginx.

### 設定例 / Example configuration

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 静的ファイル / Static files
    location /static/ {
        alias /path/to/wiwa/static/;
    }

    # テーマファイル / Theme files
    location /themes/ {
        alias /path/to/wiwa/themes/;
    }

    # アップロード画像 / Uploaded images
    location /uploads/image/ {
        alias /path/to/wiwa/uploads/image/;
    }

    # アップロードファイル（PDF） / Uploaded files (PDF)
    location /uploads/file/ {
        alias /path/to/wiwa/uploads/file/;
    }

    # アップロードサイズ制限 / Upload size limit
    client_max_body_size 20M;
}

※ `/path/to/wiwa/` は自分の環境に合わせて変更してください  
Replace `/path/to/wiwa/` with the actual path for your environment

---


## ルーティング仕様 / Routing specification

### 処理フロー / Request flow

1. `application()` が Request を生成
2. `resolve_route()` がルートを解決（extension → core）
3. `check_access()` で認証・認可を判定
4. `Dispatcher.dispatch()` がハンドラを実行
5. コントローラで `renderer.render_route()` を呼び出し
6. `route.template`（あれば）またはデフォルトテンプレートを描画

---

### ルート解決順 / Resolution order

1. Extension route（`url` + `method` 一致）
2. Static route（例: `/admin/post/list` → `admin.post.list`）
3. Dynamic route（例: `/post/hello-world` → `post.slug`）
4. Page fallback（例: `/about` → `page.slug`）

---

### Routeオブジェクト / Route object

`route` は以下のキーを持つ辞書です（`template` は任意）。

- `handler: str`
- `params: dict[str, str]`
- `method: str`
- `auth_required: bool`
- `roles: list[str]`
- `template: str` (optional)

---

### テンプレート決定ルール / Template decision

`render_route(route, default_template, ...)` は次の順でテンプレートを決定します。

1. `route["template"]` があればそれを使用
2. なければ `default_template` を使用

---

## 設計思想 / Philosophy

* No magic. Just code.()
* URLと処理は1対1  
  One URL maps to one handler
* Pythonが書ければ理解できる  
  If you can write Python, you can understand everything
* ソースコードがそのままドキュメント  
  The source code is the documentation

---

## 注意事項 / Notes

* SVGはセキュリティ上禁止  
  SVG is disabled for security reasons

* 大容量ファイルは対象外  
  Large files (video, zip, etc.) are out of scope

* サイズ制限あり（config.py参照）  
  File size limits are defined in config.py

---

## ライセンス / License

MIT License
