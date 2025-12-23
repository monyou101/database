# database.py - MySQL 資料庫操作
import os
import threading
from mysql.connector import pooling

TMDB_IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"

db_pool = None

def _init_pool_connections():
    """後台非同步初始化連線池
    在應用啟動後觸發，不阻塞應用啟動
    """
    global db_pool
    
    def _async_init():
        try:
            # 在後台非同步建立 3 個連線
            init_count = min(3, int(os.getenv("MYSQL_POOL_SIZE", 20)))
            for i in range(init_count):
                try:
                    conn = db_pool.get_connection()
                    conn.close()
                    print(f"[INIT] Pool connection {i+1}/{init_count} ready")
                except Exception as e:
                    print(f"[INIT] Warning: Failed to initialize connection {i+1}: {e}")
        except Exception as e:
            print(f"[INIT] Warning: Async pool initialization error: {e}")
    
    # 在後台執行，不阻塞主線程
    thread = threading.Thread(target=_async_init, daemon=True)
    thread.start()

def init_db_pool():
    """初始化資料庫連線池"""
    global db_pool
    db_pool = pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=int(os.getenv("MYSQL_POOL_SIZE", 20)),  # 增加到 20，預先建立連線
        pool_reset_session=False,  # 禁用連線重置，避免預初始化的連線被銷毀
        host=os.getenv("MYSQLHOST", "localhost"),
        database=os.getenv("MYSQLDATABASE", "mydb"),
        user=os.getenv("MYSQLUSER", "myuser"),
        password=os.getenv("MYSQLPASSWORD", "myuser"),
        port=int(os.getenv("MYSQLPORT", 3306)),
        autocommit=True  # 自動提交，減少往返
    )

def connect_db():
    """從連線池獲取連線"""
    global db_pool
    if db_pool is None:
        init_db_pool()
    return db_pool.get_connection()

# ==================== 內部工具函數 ====================

def check_movie(cur, tmdb_id):
    cur.execute("SELECT movie_id FROM MOVIE WHERE tmdb_id=%s", (tmdb_id,))
    row = cur.fetchone()
    return row[0] if row else None

def upsert_movie(cur, tmdb_id, title, release_year, genre, runtime, overview, rating, poster_url=None):
    cur.execute(
        """
        INSERT INTO MOVIE (tmdb_id, title, release_year, genre, runtime, overview, rating, poster_url)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
          movie_id=LAST_INSERT_ID(movie_id),
          title=COALESCE(VALUES(title), title),
          release_year=COALESCE(VALUES(release_year), release_year),
          genre=COALESCE(VALUES(genre), genre),
          runtime=COALESCE(VALUES(runtime), runtime),
          overview=COALESCE(VALUES(overview), overview),
          rating=COALESCE(VALUES(rating), rating),
          poster_url=COALESCE(VALUES(poster_url), poster_url)
        """,
        (tmdb_id, title, release_year, genre, runtime, overview, rating, poster_url),
    )
    return cur.lastrowid

def check_actor(cur, tmdb_id):
    cur.execute("SELECT actor_id FROM ACTOR WHERE tmdb_id=%s", (tmdb_id,))
    row = cur.fetchone()
    return row[0] if row else None

def upsert_actor(cur, tmdb_id, name, profile_url=None):
    cur.execute(
        """
        INSERT INTO ACTOR (tmdb_id, name, profile_url)
        VALUES (%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            actor_id=LAST_INSERT_ID(actor_id),
            name=VALUES(name),
            profile_url=VALUES(profile_url)
    """,
        (tmdb_id, name, profile_url),
    )
    return cur.lastrowid

def upsert_actor_detail(cur, tmdb_id, name, profile_url=None, birthdate=None, country=None):
    cur.execute(
        """
        INSERT INTO ACTOR (tmdb_id, name, profile_url, birthdate, country)
        VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            actor_id=LAST_INSERT_ID(actor_id),
            name=COALESCE(VALUES(name), name),
            profile_url=COALESCE(VALUES(profile_url), profile_url),
            birthdate=COALESCE(VALUES(birthdate), birthdate),
            country=COALESCE(VALUES(country), country)
    """,
        (tmdb_id, name, profile_url, birthdate, country),
    )
    return cur.lastrowid

def ensure_movie_cast(cur, movie_id, actor_id, character_name, billing_order):
    cur.execute("""
        INSERT IGNORE INTO MOVIE_CAST (movie_id, actor_id, character_name, billing_order)
        VALUES (%s,%s,%s,%s)
    """, (movie_id, actor_id, character_name, billing_order))

def ensure_director(cur, movie_id, actor_id):
    cur.execute("""
        INSERT IGNORE INTO DIRECTOR (movie_id, actor_id)
        VALUES (%s,%s)
    """, (movie_id, actor_id))

# ==================== 公開 API ====================

def get_tmdb_id_from_movie_id(movie_id):
    """從 movie_id 獲取 tmdb_id"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT tmdb_id FROM MOVIE WHERE movie_id = %s", (movie_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def get_movies_by_tmdb_ids(tmdb_ids):
    """批次獲取電影"""
    if not tmdb_ids:
        return {}
    
    conn = connect_db()
    try:
        cur = conn.cursor(dictionary=True)
        placeholders = ','.join(['%s'] * len(tmdb_ids))
        cur.execute(f"""
            SELECT movie_id, tmdb_id, title, release_year, genre, rating, poster_url
            FROM MOVIE
            WHERE tmdb_id IN ({placeholders})
            ORDER BY FIELD(tmdb_id, {placeholders})
        """, tmdb_ids + tmdb_ids)
        
        results = cur.fetchall()
        return {row['tmdb_id']: row for row in results}
    finally:
        cur.close()
        conn.close()

def get_movie_ids_from_tmdb_ids(tmdb_ids):
    """從多個 tmdb_id 批次獲取 movie_id，回傳 dict"""
    if not tmdb_ids:
        return {}
    conn = connect_db()
    cur = conn.cursor()
    try:
        placeholders = ','.join(['%s'] * len(tmdb_ids))
        cur.execute(
            f"SELECT tmdb_id, movie_id FROM MOVIE WHERE tmdb_id IN ({placeholders})",
            tmdb_ids
        )
        rows = cur.fetchall()
        return {tid: mid for tid, mid in rows}
    finally:
        cur.close()
        conn.close()

def check_movie_detail(movie_id):
    if movie_id is not None:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT poster_url, runtime FROM MOVIE WHERE movie_id=%s", (movie_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            if row[0] is None:
                return True
            elif row[1] is None:
                return False
            else:
                return True
    return False

def get_tmdb_id_from_actor_id(actor_id):
    """從 actor_id 獲取 tmdb_id"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT tmdb_id FROM ACTOR WHERE actor_id = %s", (actor_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def get_actors_by_tmdb_ids(tmdb_ids):
    """批次獲取演員"""
    if not tmdb_ids:
        return {}
    
    conn = connect_db()
    try:
        cur = conn.cursor(dictionary=True)
        placeholders = ','.join(['%s'] * len(tmdb_ids))
        cur.execute(f"""
            SELECT actor_id, tmdb_id, name, birthdate, country, profile_url
            FROM ACTOR
            WHERE tmdb_id IN ({placeholders})
            ORDER BY FIELD(tmdb_id, {placeholders})
        """, tmdb_ids + tmdb_ids)
        
        results = cur.fetchall()
        return {row['tmdb_id']: row for row in results}
    finally:
        cur.close()
        conn.close()

def get_actor_id_from_tmdb_id(tmdb_id):
    """從 tmdb_id 獲取 actor_id"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT actor_id FROM ACTOR WHERE tmdb_id = %s", (tmdb_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def check_actor_update(actor_id):
    check_detail = False
    check_movie = False
    if actor_id is not None:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT profile_url, birthdate, updated_at FROM ACTOR WHERE actor_id=%s", (actor_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            if row[2] is not None:
                # 計算時間差是否在 24 小時內
                from datetime import datetime, timedelta
                updated_at = row[2]
                if datetime.now() - updated_at < timedelta(days=1):
                    check_movie = True
                check_detail = True
            else:
                if row[0] is None:
                    check_detail = True
                elif row[1] is not None:
                    check_detail = True
    return [check_detail, check_movie]

def update_actor_time(actor_id):
    if actor_id is not None:
        conn = connect_db()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE ACTOR SET updated_at = CURRENT_TIMESTAMP WHERE actor_id=%s",
                (actor_id,)
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

def normalize_movie_row(row):
    if not row: return None
    return {
        'movie_id': row.get('movie_id') if isinstance(row, dict) else row[0],
        'title': row.get('title') if isinstance(row, dict) else row[1],
        'release_year': row.get('release_year') if isinstance(row, dict) else row[2],
        'genre': row.get('genre') if isinstance(row, dict) else row[3],
        'rating': row.get('rating') if isinstance(row, dict) else row[4],
        'poster_url': row.get('poster_url') if isinstance(row, dict) else row[5]
    }

def normalize_actor_row(row):
    if not row: return None
    return {
        'actor_id': row.get('actor_id') if isinstance(row, dict) else row[0],
        'name': row.get('name') if isinstance(row, dict) else row[1],
        'birthdate': row.get('birthdate') if isinstance(row, dict) else row[2],
        'country': row.get('country') if isinstance(row, dict) else row[3],
        'profile_url': row.get('profile_url') if isinstance(row, dict) else row[4]
    }

# ==================== 存儲函數 ====================

def store_movie(tmdb_movie_id, movie_data):
    """將 TMDB 電影資料存入資料庫"""
    conn = connect_db()
    cur = conn.cursor()

    # movie_id = check_movie(cur, tmdb_movie_id)
    # if check_movie_detail(movie_id):
    #     print(f"Movie with tmdb_id {tmdb_movie_id} already exists, skipping.")
    #     cur.close()
    #     conn.close()
    #     return movie_id

    try:
        title = movie_data.get("title")
        release_year = None
        if movie_data.get("release_date"):
            release_year = movie_data["release_date"].split("-")[0]
        genres = ", ".join([g["name"] for g in movie_data.get("genres", [])]) if movie_data.get("genres") else None
        runtime = movie_data.get("runtime")
        overview = movie_data.get("overview")
        rating = movie_data.get("vote_average")
        poster_path = movie_data.get("poster_path")
        poster_url = f"{TMDB_IMG_BASE_URL}{poster_path}" if poster_path else None

        movie_id = upsert_movie(cur, tmdb_movie_id, title, release_year, genres, runtime, overview, rating, poster_url)

        credits = movie_data.get("credits", {})

        cast_members = credits.get("cast", [])[:20]
        crew_members = credits.get("crew", [])[:20]

        tmdb_to_basic = {}
        for m in cast_members:
            tid = m.get("id")
            if tid:
                pp = m.get("profile_path")
                tmdb_to_basic[tid] = (
                    m.get("name"),
                    f"{TMDB_IMG_BASE_URL}{pp}" if pp else None,
                )
        director_ids = []
        for m in crew_members:
            if m.get("job") == "Director":
                tid = m.get("id")
                if tid:
                    director_ids.append(tid)
                    if tid not in tmdb_to_basic:
                        pp = m.get("profile_path")
                        tmdb_to_basic[tid] = (
                            m.get("name"),
                            f"{TMDB_IMG_BASE_URL}{pp}" if pp else None,
                        )

        all_tmdb_ids = list(tmdb_to_basic.keys())
        actor_id_map = {}
        if all_tmdb_ids:
            placeholders = ",".join(["%s"] * len(all_tmdb_ids))
            cur.execute(
                f"SELECT tmdb_id, actor_id FROM ACTOR WHERE tmdb_id IN ({placeholders})",
                all_tmdb_ids,
            )
            for tid, aid in cur.fetchall() or []:
                actor_id_map[tid] = aid

            missing = [tid for tid in all_tmdb_ids if tid not in actor_id_map]
            if missing:
                values = [(tid, tmdb_to_basic[tid][0], tmdb_to_basic[tid][1]) for tid in missing]
                cur.executemany(
                    """
                    INSERT INTO ACTOR (tmdb_id, name, profile_url)
                    VALUES (%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                        name=VALUES(name),
                        profile_url=VALUES(profile_url)
                    """,
                    values,
                )
                cur.execute(
                    f"SELECT tmdb_id, actor_id FROM ACTOR WHERE tmdb_id IN ({placeholders})",
                    all_tmdb_ids,
                )
                for tid, aid in cur.fetchall() or []:
                    actor_id_map[tid] = aid

        if cast_members and actor_id_map:
            cast_rows = []
            for m in cast_members:
                tid = m.get("id")
                aid = actor_id_map.get(tid)
                if aid:
                    cast_rows.append(
                        (movie_id, aid, m.get("character"), m.get("order"))
                    )
            if cast_rows:
                cur.executemany(
                    """
                    INSERT IGNORE INTO MOVIE_CAST (movie_id, actor_id, character_name, billing_order)
                    VALUES (%s,%s,%s,%s)
                    """,
                    cast_rows,
                )

        if director_ids and actor_id_map:
            dir_rows = []
            for tid in director_ids:
                aid = actor_id_map.get(tid)
                if aid:
                    dir_rows.append((movie_id, aid))
            if dir_rows:
                cur.executemany(
                    """
                    INSERT IGNORE INTO DIRECTOR (movie_id, actor_id)
                    VALUES (%s,%s)
                    """,
                    dir_rows,
                )

        conn.commit()
        return movie_id
        
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def store_actor(tmdb_actor_id, actor_data):
    """將 TMDB 演員資料存入資料庫"""
    conn = connect_db()
    cur = conn.cursor()

    # actor_id = check_actor(cur, tmdb_actor_id)
    # if check_actor_detail(actor_id):
    #     print(f"Actor with tmdb_id {tmdb_actor_id} already exists, skipping.")
    #     cur.close()
    #     conn.close()
    #     return actor_id

    try:
        # 解析演員資訊
        name = actor_data.get("name")
        profile_path = actor_data.get("profile_path")
        profile_url = f"{TMDB_IMG_BASE_URL}{profile_path}" if profile_path else None
        birthdate = actor_data.get("birthday")
        country = actor_data.get("place_of_birth")
        
        # 儲存演員詳細資訊
        actor_id = upsert_actor_detail(cur, tmdb_actor_id, name, profile_url, birthdate, country)
        
        conn.commit()
        return actor_id
        
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def insert_movie_cast_batch(actor_id, movie_ids, cast_members):
    """批次更新/插入 MOVIE_CAST"""
    conn = connect_db()
    cur = conn.cursor()

    try:
        cast_rows = []
        for m in cast_members:
            tid = m.get("id")
            mid = movie_ids.get(tid)
            if mid:
                cast_rows.append(
                    (mid, actor_id, m.get("character"), m.get("order"))
                )
        if cast_rows:
            cur.executemany(
                """
                INSERT IGNORE INTO MOVIE_CAST (movie_id, actor_id, character_name, billing_order)
                VALUES (%s,%s,%s,%s)
                """,
                cast_rows,
            )
        
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def insert_directors_batch(actor_id, movie_ids):
    """批次更新/插入 DIRECTOR"""
    conn = connect_db()
    cur = conn.cursor()

    try:
        dir_rows = []
        for mid in movie_ids:
            dir_rows.append((mid, actor_id))
        if dir_rows:
            cur.executemany(
                """
                INSERT IGNORE INTO DIRECTOR (movie_id, actor_id)
                VALUES (%s,%s)
                """,
                dir_rows,
            )
        
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

# ==================== 用戶管理 ====================

def create_user(username, email, password_hash):
    """建立新用戶，存入正確的暱稱"""
    conn = connect_db()
    cur = conn.cursor()
    try:
        # 修改 SQL，將傳進來的 username 存入 username 欄位
        cur.execute("INSERT INTO USER (username, email, password_hash) VALUES (%s, %s, %s)", 
                    (username, email, password_hash))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_user_by_email(email, password_hash):
    """根據 email 和密碼獲取用戶"""
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_id, username FROM USER WHERE email = %s AND password_hash = %s", (email, password_hash))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

# ==================== 電影查詢 ====================

def search_movies(query, page=1, limit=20):
    """搜尋電影"""
    offset = (page - 1) * limit
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    if query:
        sql = """
            SELECT movie_id, title, release_year, genre, rating, poster_url
            FROM MOVIE
            WHERE title LIKE %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(sql, (f'%{query}%', limit, offset))
    else:
        sql = """
            SELECT movie_id, title, release_year, genre, rating, poster_url
            FROM MOVIE
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(sql, (limit, offset))
    movies = cur.fetchall()
    
    cur.close()
    conn.close()
    return movies

def get_movie_detail(movie_id):
    """獲取電影詳細資訊（含演員、導演、評論）"""
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    cur.execute("SELECT * FROM MOVIE WHERE movie_id = %s", (movie_id,))
    movie = cur.fetchone()
    if not movie:
        cur.close()
        conn.close()
        return None
    
    cur.execute("""
        SELECT a.actor_id, a.name, a.birthdate, a.country, a.profile_url, mc.character_name, mc.billing_order
        FROM ACTOR a
        JOIN MOVIE_CAST mc ON a.actor_id = mc.actor_id
        WHERE mc.movie_id = %s
        ORDER BY mc.billing_order
    """, (movie_id,))
    movie['actors'] = cur.fetchall()
    
    cur.execute("""
        SELECT a.actor_id, a.name, a.birthdate, a.country, a.profile_url
        FROM ACTOR a
        JOIN DIRECTOR d ON a.actor_id = d.actor_id
        WHERE d.movie_id = %s
    """, (movie_id,))
    movie['directors'] = cur.fetchall()
    
    cur.execute("""
        SELECT r.review_id, r.rating, r.title, r.body, r.created_at, u.username
        FROM REVIEW r
        JOIN USER u ON r.user_id = u.user_id
        WHERE r.target_type = 'MOVIE' AND r.target_id = %s
        ORDER BY r.created_at DESC
    """, (movie_id,))
    movie['reviews'] = cur.fetchall()
    
    cur.close()
    conn.close()
    return movie

# ==================== 演員查詢 ====================

def search_actors(query, page=1, limit=20):
    """搜尋演員"""
    offset = (page - 1) * limit
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    if query:
        sql = """
            SELECT actor_id, name, birthdate, country, profile_url
            FROM ACTOR
            WHERE name LIKE %s
            ORDER BY name
            LIMIT %s OFFSET %s
        """
        cur.execute(sql, (f'%{query}%', limit, offset))
    else:
        sql = """
            SELECT actor_id, name, birthdate, country, profile_url
            FROM ACTOR
            ORDER BY name
            LIMIT %s OFFSET %s
        """
        cur.execute(sql, (limit, offset))
    actors = cur.fetchall()
    
    cur.close()
    conn.close()
    return actors

def get_actor_detail(actor_id):
    """獲取演員詳細資訊（含參演電影）"""
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    cur.execute("SELECT * FROM ACTOR WHERE actor_id = %s", (actor_id,))
    actor = cur.fetchone()
    if not actor:
        cur.close()
        conn.close()
        return None
    
    cur.execute("""
        SELECT m.movie_id, m.title, m.release_year, m.genre, m.rating, m.poster_url, mc.character_name
        FROM MOVIE m
        JOIN MOVIE_CAST mc ON m.movie_id = mc.movie_id
        WHERE mc.actor_id = %s
        ORDER BY m.release_year DESC
    """, (actor_id,))
    actor['movies_as_actor'] = cur.fetchall()
    
    cur.execute("""
        SELECT m.movie_id, m.title, m.release_year, m.genre, m.rating, m.poster_url
        FROM MOVIE m
        JOIN DIRECTOR d ON m.movie_id = d.movie_id
        WHERE d.actor_id = %s
        ORDER BY m.release_year DESC
    """, (actor_id,))
    actor['movies_as_director'] = cur.fetchall()
    
    cur.close()
    conn.close()
    return actor

# ==================== 評論管理 ====================

def add_review(user_id, target_type, target_id, rating, title, body):
    """新增或更新評論"""
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO REVIEW (user_id, target_type, target_id, rating, title, body)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE rating=VALUES(rating), title=VALUES(title), body=VALUES(body)
        """, (user_id, target_type, target_id, rating, title, body))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_movie_reviews(movie_id):
    """獲取電影評論"""
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    cur.execute("""
        SELECT r.review_id, r.rating, r.title, r.body, r.created_at, u.username, u.email
        FROM REVIEW r
        JOIN USER u ON r.user_id = u.user_id
        WHERE r.target_type = 'MOVIE' AND r.target_id = %s
        ORDER BY r.created_at DESC
    """, (movie_id,))
    reviews = cur.fetchall()
    
    cur.close()
    conn.close()
    return reviews

# ==================== SQL 指令執行 ====================

def execute_sql_query(command):
    """執行 SQL 查詢（僅限 SELECT）"""
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        cur.execute(command)
        results = cur.fetchall()
        return results
    except Exception as e:
        raise e
    finally:
        cur.close()
        conn.close()