這個專案是一個電影資料庫系統，使用 TMDB API 抓取電影資料，儲存到 MySQL 資料庫，並提供 Flask 後端 API 與前端介面查詢。

## 概述
- **後端**：Flask API，處理資料庫查詢與 TMDB 自動下載。
- **前端**：靜態 HTML/JS，顯示電影清單與詳細頁。
- **資料庫**：MySQL，儲存電影、演員、評論等。
- **API**：TMDB，用於抓取電影資料。

## 系統需求
- Python 3.8+
- MySQL 8.0+
- 網路連線（存取 TMDB API）
- 瀏覽器（Chrome/Edge 推薦）

## 安裝

### Ubuntu
1. **更新系統**：
   ````bash
   sudo apt update && sudo apt upgrade -y
   ````

2. **安裝 Python 與 pip**：
   ````bash
   sudo apt install python3 python3-pip python3-venv -y
   ````

3. **安裝 MySQL**：
   ````bash
   sudo apt install mysql-server -y
   sudo systemctl start mysql
   sudo mysql_secure_installation
   ````

4. **建立專案目錄並進入**：
   ````bash
   mkdir ~/movie_db && cd ~/movie_db
   ````

5. **複製專案檔案**（假設從 Git 或手動複製）：
   ````bash
   # 複製所有檔案到 ~/movie_db
   ````

6. **建立虛擬環境**：
   ````bash
   python3 -m venv venv
   source venv/bin/activate
   ````

7. **安裝 Python 依賴**：
   ````bash
   pip install flask flask-cors mysql-connector-python requests
   ````

8. **設定 MySQL 資料庫**：
   ````bash
   sudo mysql -u root -p
   ````
   在 MySQL shell 中：
   ````sql
   CREATE DATABASE mydb;
   CREATE USER 'myuser'@'localhost' IDENTIFIED BY 'myuser';
   GRANT ALL PRIVILEGES ON mydb.* TO 'myuser'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ````
   然後匯入 schema：
   ````bash
   mysql -u myuser -p mydb < MySQL.session.sql
   ````

### Windows
1. **下載並安裝 Python**：
   - 前往 https://www.python.org/downloads/ 下載 Python 3.8+。
   - 安裝時勾選 "Add Python to PATH"。

2. **下載並安裝 MySQL**：
   - 前往 https://dev.mysql.com/downloads/mysql/ 下載 MySQL Installer。
   - 安裝 MySQL Server，設定 root 密碼。

3. **建立專案目錄**：
   - 在 C:\ 或桌面建立資料夾 `movie_db`，進入。

4. **複製專案檔案**（從 Git 或手動）。

5. **建立虛擬環境**：
   ````cmd
   python -m venv venv
   venv\Scripts\activate
   ````

6. **安裝 Python 依賴**：
   ````cmd
   pip install flask flask-cors mysql-connector-python requests
   ````

7. **設定 MySQL 資料庫**：
   - 開啟 MySQL Command Line Client。
   ````sql
   CREATE DATABASE mydb;
   CREATE USER 'myuser'@'localhost' IDENTIFIED BY 'myuser';
   GRANT ALL PRIVILEGES ON mydb.* TO 'myuser'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ````
   然後匯入 schema：
   ````cmd
   mysql -u myuser -p mydb < MySQL.session.sql
   ````

## 設定
1. **環境變數**：
   - 建立 `.env` 檔案（或直接設定）：
     ````
     TMDB_API_KEY=your_tmdb_api_key_here
     DB_HOST=localhost
     DB_USER=myuser
     DB_PASS=myuser
     DB_NAME=mydb
     ````
   - TMDB API key 從 https://www.themoviedb.org/settings/api 取得。

2. **確認連線**：
   - Ubuntu：`mysql -u myuser -p mydb -e "SHOW TABLES;"`
   - Windows：同上，在 cmd 中。

## 執行應用程式
1. **啟動後端**：
   - Ubuntu：`source venv/bin/activate && python movie_backend.py`
   - Windows：`venv\Scripts\activate && python movie_backend.py`
   - 後端在 http://127.0.0.1:5000 運行。

2. **啟動前端**：
   - 進入 Movie_UI 資料夾。
   - Ubuntu：`python3 -m http.server 8000`
   - Windows：`python -m http.server 8000`
   - 前端在 http://127.0.0.1:8000 運行。

3. **測試**：
   - 訪問 http://127.0.0.1:8000/index.html 查看電影清單。
   - 訪問 http://127.0.0.1:8000/movie.html?id=550 查看電影詳細。

## 使用說明
- **抓取資料**：執行 `python fetch_tmdb.py popular 5` 抓取熱門電影。
- **搜尋**：在前端搜尋欄輸入關鍵字，或使用 `python fetch_tmdb.py search movie "Inception"`。
- **API**：直接訪問 http://127.0.0.1:5000/movies/tmdb/550（若無，自動下載）。

## 故障排除
- **MySQL 連線錯誤**：檢查環境變數與 MySQL 服務狀態。
- **TMDB API 錯誤**：確認 API key 正確，檢查網路。
- **前端載入失敗**：確保後端運行，檢查 CORS。
- **資料庫錯誤**：若 "Data too long"，參考前述 ALTER TABLE。
- **Windows 路徑**：使用 `\` 而非 `/`。

若有問題，提供錯誤訊息以進一步協助。   - TMDB API key 從 https://www.themoviedb.org/settings/api 取得。

2. **確認連線**：
   - Ubuntu：`mysql -u myuser -p mydb -e "SHOW TABLES;"`
   - Windows：同上，在 cmd 中。

## 執行應用程式
1. **啟動後端**：
   - Ubuntu：`source venv/bin/activate && python movie_backend.py`
   - Windows：`venv\Scripts\activate && python movie_backend.py`
   - 後端在 http://127.0.0.1:5000 運行。

2. **啟動前端**：
   - 進入 Movie_UI 資料夾。
   - Ubuntu：`python3 -m http.server 8000`
   - Windows：`python -m http.server 8000`
   - 前端在 http://127.0.0.1:8000 運行。

3. **測試**：
   - 訪問 http://127.0.0.1:8000/index.html 查看電影清單。
   - 訪問 http://127.0.0.1:8000/movie.html?id=550 查看電影詳細。

## 使用說明
- **抓取資料**：執行 `python fetch_tmdb.py popular 5` 抓取熱門電影。
- **搜尋**：在前端搜尋欄輸入關鍵字，或使用 `python fetch_tmdb.py search movie "Inception"`。
- **API**：直接訪問 http://127.0.0.1:5000/movies/tmdb/550（若無，自動下載）。

## 故障排除
- **MySQL 連線錯誤**：檢查環境變數與 MySQL 服務狀態。
- **TMDB API 錯誤**：確認 API key 正確，檢查網路。
- **前端載入失敗**：確保後端運行，檢查 CORS。
- **資料庫錯誤**：若 "Data too long"，參考前述 ALTER TABLE。
- **Windows 路徑**：使用 `\` 而非 `/`。
