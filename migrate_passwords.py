#!/usr/bin/env python3
"""
簡易密碼遷移腳本
- 目的：將 USER.password_hash 欄位中可能為明文的值，轉換為安全的雜湊（PBKDF2-SHA256）。
- 依賴：Flask 依賴的 Werkzeug 已在 requirements 中（flask），不用額外安裝。
- 連線設定：由環境變數讀取 MYSQL* 設定（與應用一致）。

使用範例：
    乾跑（僅統計，不更新）
        python migrate_passwords.py --dry-run
    實際遷移（更新資料庫）
        python migrate_passwords.py

安全注意：
- 無法從 NULL 或未知值恢復明文密碼，若遇到 NULL 會跳過並提示。
- 以啟發式判斷是否已是雜湊（例如以 'pbkdf2:' 開頭），避免重複雜湊。
"""

import os
import argparse
import sys
from typing import Tuple
import mysql.connector
from werkzeug.security import generate_password_hash


def get_db_conn():
    conn = mysql.connector.connect(
        host=os.getenv("MYSQLHOST", "localhost"),
        database=os.getenv("MYSQLDATABASE", "mydb"),
        user=os.getenv("MYSQLUSER", "myuser"),
        password=os.getenv("MYSQLPASSWORD", "myuser"),
        port=int(os.getenv("MYSQLPORT", 3306)),
    )
    return conn


def is_probably_hashed(value: str) -> bool:
    """判斷字串是否看起來已是 Werkzeuge 風格的雜湊。
    常見格式：pbkdf2:sha256:...$salt$hash 或 scrypt:... 等。
    """
    if not value:
        return False
    v = value.strip()
    if v.startswith("pbkdf2:") or v.startswith("scrypt:"):
        return True
    # 其他常見雜湊格式（保守判斷）：含多個分隔符與長度較長
    if ":" in v and "$" in v and len(v) > 40:
        return True
    return False


def migrate(dry_run: bool = True) -> Tuple[int, int, int]:
    conn = get_db_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT user_id, username, email, password_hash FROM USER")
    rows = cur.fetchall() or []

    total = len(rows)
    already_hashed = 0
    migrated = 0

    to_update = []
    for row in rows:
        uid = row["user_id"]
        ph = row.get("password_hash")
        if ph is None or ph == "":
            print(f"[SKIP] user_id={uid} email={row['email']} 無密碼資料，無法遷移")
            continue
        if is_probably_hashed(ph):
            already_hashed += 1
            continue
        # 視為明文，產生雜湊
        new_hash = generate_password_hash(ph)
        to_update.append((new_hash, uid))

    if dry_run:
        print(f"[DRY-RUN] 將更新 {len(to_update)} 筆，已雜湊 {already_hashed} 筆，總計 {total} 筆")
    else:
        if to_update:
            cur.executemany(
                "UPDATE USER SET password_hash=%s WHERE user_id=%s",
                to_update,
            )
            conn.commit()
            migrated = len(to_update)
            print(f"[DONE] 已更新 {migrated} 筆，已雜湊 {already_hashed} 筆，總計 {total} 筆")
        else:
            print(f"[DONE] 無需更新，已雜湊 {already_hashed} 筆，總計 {total} 筆")

    cur.close()
    conn.close()
    return total, already_hashed, migrated


def main():
    parser = argparse.ArgumentParser(description="簡易密碼遷移腳本")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="僅統計與預覽，不寫入資料庫",
    )
    args = parser.parse_args()

    try:
        migrate(dry_run=args.dry_run)
    except mysql.connector.Error as e:
        print(f"[ERROR] MySQL 連線/執行錯誤: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 未預期錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
