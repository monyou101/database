#!/usr/bin/env python3
"""在 Railway 環境中執行效能測試"""
import os
import sys

# 確保在 Railway 環境中
os.chdir('/code') if os.path.exists('/code') else os.chdir('/home/ono/database')

# 執行測試
if __name__ == '__main__':
    import time
    print("=" * 60)
    print("Railway 資料庫效能測試（Railway 環境）")
    print("=" * 60)
    print()
    
    try:
        from database import get_tmdb_id_from_movie_id, get_movie_detail, check_movie_detail
        
        movie_id = 281
        print(f"測試電影 ID: {movie_id}")
        print("-" * 60)
        
        # 測試 1
        start = time.time()
        tmdb_id = get_tmdb_id_from_movie_id(movie_id)
        t1 = time.time() - start
        print(f"1. get_tmdb_id_from_movie_id: {t1:.3f}s -> {tmdb_id}")
        
        # 測試 2
        start = time.time()
        check_result = check_movie_detail(movie_id)
        t2 = time.time() - start
        print(f"2. check_movie_detail: {t2:.3f}s -> {check_result}")
        
        # 測試 3
        start = time.time()
        movie = get_movie_detail(movie_id)
        t3 = time.time() - start
        print(f"3. get_movie_detail: {t3:.3f}s")
        if movie:
            print(f"   - 標題: {movie.get('title')}")
            print(f"   - 演員: {len(movie.get('actors', []))} 人")
            print(f"   - 導演: {len(movie.get('directors', []))} 人")
            print(f"   - 評論: {len(movie.get('reviews', []))} 筆")
        
        total = t1 + t2 + t3
        print()
        print("=" * 60)
        print(f"總計: {total:.3f}s")
        print("=" * 60)
        
        if total > 15:
            print("❌ 超過 15 秒 - 極度緩慢")
        elif total > 5:
            print("⚠️  超過 5 秒 - 需要優化")
        elif total > 1:
            print("⚠️  超過 1 秒 - 可接受但不理想")
        else:
            print("✓ 良好 - 少於 1 秒")
        
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
