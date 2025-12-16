#!/usr/bin/env python3
"""
Railway 環境效能測試腳本
測試資料庫查詢速度、連線延遲等
"""
import time
import os
import sys

print("=" * 60)
print("Railway 資料庫效能測試")
print("=" * 60)
print()

# 1. 檢查環境變數
print("1. 環境變數檢查")
print("-" * 60)
required_vars = ['MYSQLHOST', 'MYSQLDATABASE', 'MYSQLUSER', 'MYSQLPASSWORD', 'MYSQLPORT']
for var in required_vars:
    val = os.getenv(var, 'NOT SET')
    if var == 'MYSQLPASSWORD':
        val = '***' if val != 'NOT SET' else val
    print(f"  {var}: {val}")
print()

# 2. 測試資料庫連線
print("2. 資料庫連線測試")
print("-" * 60)
try:
    import mysql.connector
    
    start = time.time()
    conn = mysql.connector.connect(
        host=os.getenv('MYSQLHOST', 'localhost'),
        database=os.getenv('MYSQLDATABASE', 'mydb'),
        user=os.getenv('MYSQLUSER', 'myuser'),
        password=os.getenv('MYSQLPASSWORD', 'myuser'),
        port=int(os.getenv('MYSQLPORT', 3306))
    )
    connect_time = time.time() - start
    print(f"  ✓ 連線成功: {connect_time:.3f}s")
    
    # 3. 簡單查詢測試
    print()
    print("3. 簡單查詢測試")
    print("-" * 60)
    cur = conn.cursor()
    
    # 查詢 A: COUNT
    start = time.time()
    cur.execute('SELECT COUNT(*) FROM MOVIE')
    result = cur.fetchone()
    query_a_time = time.time() - start
    print(f"  SELECT COUNT(*) FROM MOVIE: {query_a_time:.3f}s")
    print(f"    結果: {result[0]} 筆")
    
    # 查詢 B: 取得單一電影
    start = time.time()
    cur.execute('SELECT * FROM MOVIE WHERE movie_id = 281')
    movie = cur.fetchone()
    query_b_time = time.time() - start
    if movie:
        print(f"  SELECT * FROM MOVIE WHERE movie_id=281: {query_b_time:.3f}s")
        print(f"    標題: {movie[2]}")
    else:
        print(f"  SELECT * FROM MOVIE WHERE movie_id=281: {query_b_time:.3f}s (無結果)")
    
    # 4. 複雜查詢測試 (模擬 get_movie_detail)
    print()
    print("4. 複雜查詢測試 (模擬 get_movie_detail)")
    print("-" * 60)
    
    queries = [
        ("主電影資訊", "SELECT * FROM MOVIE WHERE movie_id = 281"),
        ("演員陣容", """SELECT a.actor_id, a.name FROM ACTOR a 
            JOIN MOVIE_CAST mc ON a.actor_id = mc.actor_id 
            WHERE mc.movie_id = 281 ORDER BY mc.billing_order"""),
        ("導演", """SELECT a.actor_id, a.name FROM ACTOR a 
            JOIN DIRECTOR d ON a.actor_id = d.actor_id 
            WHERE d.movie_id = 281"""),
        ("評論", """SELECT r.review_id, u.username FROM REVIEW r 
            JOIN USER u ON r.user_id = u.user_id 
            WHERE r.target_type = 'MOVIE' AND r.target_id = 281""")
    ]
    
    total_time = 0
    for query_name, query in queries:
        start = time.time()
        cur.execute(query)
        results = cur.fetchall()
        query_time = time.time() - start
        total_time += query_time
        print(f"  {query_name}: {query_time:.3f}s ({len(results)} 筆)")
    
    print(f"  ─────────────────────────")
    print(f"  小計 (4 個查詢): {total_time:.3f}s")
    
    # 5. 連線池測試
    print()
    print("5. 連線池測試 (模擬多個請求)")
    print("-" * 60)
    
    from mysql.connector import pooling
    db_pool = pooling.MySQLConnectionPool(
        pool_name="perf_test",
        pool_size=5,
        pool_reset_session=True,
        host=os.getenv('MYSQLHOST', 'localhost'),
        database=os.getenv('MYSQLDATABASE', 'mydb'),
        user=os.getenv('MYSQLUSER', 'myuser'),
        password=os.getenv('MYSQLPASSWORD', 'myuser'),
        port=int(os.getenv('MYSQLPORT', 3306))
    )
    
    times = []
    for i in range(5):
        start = time.time()
        pool_conn = db_pool.get_connection()
        pool_cur = pool_conn.cursor()
        pool_cur.execute('SELECT * FROM MOVIE WHERE movie_id = 281')
        pool_cur.fetchone()
        pool_cur.close()
        pool_conn.close()
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  請求 {i+1}: {elapsed:.3f}s")
    
    avg_time = sum(times) / len(times)
    print(f"  ─────────────────────────")
    print(f"  平均時間: {avg_time:.3f}s")
    
    cur.close()
    conn.close()
    
    # 6. 總結
    print()
    print("6. 效能摘要")
    print("-" * 60)
    print(f"  連線延遲: {connect_time:.3f}s")
    print(f"  簡單查詢: {query_a_time:.3f}s")
    print(f"  複雜查詢 (4 個 JOIN): {total_time:.3f}s")
    print(f"  連線池平均: {avg_time:.3f}s")
    
    # 預估
    print()
    print("7. 預估 /movies/<id> 端點的完整時間")
    print("-" * 60)
    estimated = total_time + avg_time + 0.01  # 0.01s 用於 Flask 開銷
    print(f"  預估時間: ~{estimated:.3f}s")
    if estimated > 5:
        print(f"  ⚠️  警告: 超過 5 秒，可能存在效能問題")
    elif estimated > 1:
        print(f"  ⚠️  警告: 超過 1 秒")
    else:
        print(f"  ✓ 良好: 少於 1 秒")
    
except Exception as e:
    print(f"  ✗ 錯誤: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("測試完成")
print("=" * 60)
