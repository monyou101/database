# database.py - MySQL 資料庫操作
import os
import mysql.connector

TMDB_IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"

def connect_db():
    """建立資料庫連線"""
    mysql_url = os.getenv("MYSQL_URL")
    if mysql_url:
        return mysql.connector.connect(
            host=os.getenv("MYSQLHOST"),
            database=os.getenv("MYSQLDATABASE"),
            user=os.getenv("MYSQLUSER"),
            password=os.getenv("MYSQLPASSWORD"),
            port=os.getenv("MYSQLPORT", 3306)
        )
    else:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "myuser"),
            password=os.getenv("DB_PASS", "myuser"),
            database=os.getenv("DB_NAME", "mydb")
        )

def check_movie(cur, tmdb_id):
    cur.execute("SELECT movie_id FROM MOVIE WHERE tmdb_id=%s", (tmdb_id,))
    row = cur.fetchone()
    return row[0] if row else None

def upsert_movie(cur, tmdb_id, title, release_year, genre, runtime, overview, rating, poster_url=None):
    cur.execute("""
        INSERT INTO MOVIE (tmdb_id, title, release_year, genre, runtime, overview, rating, poster_url)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
          title=COALESCE(VALUES(title), title),
          release_year=COALESCE(VALUES(release_year), release_year),
          genre=COALESCE(VALUES(genre), genre),
          runtime=COALESCE(VALUES(runtime), runtime),
          overview=COALESCE(VALUES(overview), overview),
          rating=COALESCE(VALUES(rating), rating),
          poster_url=COALESCE(VALUES(poster_url), poster_url)
    """, (tmdb_id, title, release_year, genre, runtime, overview, rating, poster_url))
    # 回傳 movie_id
    cur.execute("SELECT movie_id FROM MOVIE WHERE tmdb_id=%s", (tmdb_id,))
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Failed to fetch movie_id for tmdb_id={tmdb_id}")
    print(f"Stored movie {title} (movie_id={row[0]})")
    return row[0]

def get_tmdb_id_from_movie_id(movie_id):
    """從 movie_id 獲取 tmdb_id"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT tmdb_id FROM MOVIE WHERE movie_id = %s", (movie_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def get_movie_id_from_tmdb_id(tmdb_id):
    """從 tmdb_id 獲取 movie_id"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT movie_id FROM MOVIE WHERE tmdb_id = %s", (tmdb_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def check_actor(cur, tmdb_id):
    # 先檢查是否存在，避免重複插入時消耗 AUTO_INCREMENT
    cur.execute("SELECT actor_id FROM ACTOR WHERE tmdb_id=%s", (tmdb_id,))
    row = cur.fetchone()
    if row:
        return row[0]
    return None  # 明確返回 None 若不存在

def check_actor_detail(cur, actor_id):
    if actor_id is not None:
        cur.execute("SELECT birthdate FROM ACTOR WHERE actor_id=%s", (actor_id,))
        row = cur.fetchone()
        if row and row[0] is not None:
            return True
    return False

def upsert_actor(cur, tmdb_id, name, profile_url=None):
    cur.execute("""
        INSERT INTO ACTOR (tmdb_id, name, profile_url)
        VALUES (%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            name=COALESCE(VALUES(name), name),
            profile_url=COALESCE(VALUES(profile_url), profile_url)
    """, (tmdb_id, name, profile_url))
    cur.execute("SELECT actor_id FROM ACTOR WHERE tmdb_id=%s", (tmdb_id,))
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Failed to fetch actor_id for tmdb_id={tmdb_id}")
    print(f"Stored actor {name} (actor_id={row[0]})")
    return row[0]

def get_tmdb_id_from_actor_id(actor_id):
    """從 actor_id 獲取 tmdb_id"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT tmdb_id FROM ACTOR WHERE actor_id = %s", (actor_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def get_actor_id_from_tmdb_id(tmdb_id):
    """從 tmdb_id 獲取 actor_id"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT actor_id FROM ACTOR WHERE tmdb_id = %s", (tmdb_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def upsert_actor_detail(cur, tmdb_id, name, profile_url=None, birthdate=None, country=None):
    cur.execute("""
        INSERT INTO ACTOR (tmdb_id, name, profile_url, birthdate, country)
        VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            name=COALESCE(VALUES(name), name),
            profile_url=COALESCE(VALUES(profile_url), profile_url),
            birthdate=COALESCE(VALUES(birthdate), birthdate),
            country=COALESCE(VALUES(country), country)
    """, (tmdb_id, name, profile_url, birthdate, country))
    cur.execute("SELECT actor_id FROM ACTOR WHERE tmdb_id=%s", (tmdb_id,))
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Failed to fetch actor_id for tmdb_id={tmdb_id}")
    print(f"Stored actor {name} (actor_id={row[0]})")
    return row[0]

def ensure_movie_cast(cur, movie_id, actor_id, character_name, billing_order):
    # UNIQUE (movie_id, actor_id) 已存在時 INSERT IGNORE 可以跳過
    cur.execute("""
        INSERT IGNORE INTO MOVIE_CAST (movie_id, actor_id, character_name, billing_order)
        VALUES (%s,%s,%s,%s)
    """, (movie_id, actor_id, character_name, billing_order))

def ensure_director(cur, movie_id, actor_id):
    cur.execute("""
        INSERT IGNORE INTO DIRECTOR (movie_id, actor_id)
        VALUES (%s,%s)
    """, (movie_id, actor_id))

def store_movie(tmdb_movie_id, movie_data):
    """
    將 TMDB 電影資料存入資料庫（由外部傳入已解析資料）
    
    Args:
        tmdb_movie_id: TMDB 電影 ID
        movie_data: dict，包含以下欄位：
            - title: 電影標題
            - release_date: 發行日期（YYYY-MM-DD）
            - genres: list of dict，每個 dict 有 'name' 欄位
            - runtime: 片長（分鐘）
            - overview: 簡介
            - vote_average: 評分
            - poster_path: 海報路徑
            - credits: dict，包含 'cast' 和 'crew' 陣列
    
    Returns:
        movie_id: 資料庫中的電影 ID
    """
    conn = connect_db()
    cur = conn.cursor()

    if check_movie(cur, tmdb_movie_id):
        print(f"Movie with tmdb_id {tmdb_movie_id} already exists, skipping.")
        movie_id = get_movie_id_from_tmdb_id(tmdb_movie_id)
        cur.close()
        conn.close()
        return movie_id

    try:
        # 解析電影基本資訊
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

        # 儲存電影
        movie_id = upsert_movie(cur, tmdb_movie_id, title, release_year, genres, runtime, overview, rating, poster_url)

        # 處理演員和導演
        credits = movie_data.get("credits", {})
        
        # 演員 (cast)
        for member in credits.get("cast", []):
            actor_tmdb_id = member.get("id")
            actor_id = check_actor(cur, actor_tmdb_id)
            if actor_id is None:
                actor_name = member.get("name")
                profile_path = member.get("profile_path")
                profile_url = f"{TMDB_IMG_BASE_URL}{profile_path}" if profile_path else None
                actor_id = upsert_actor(cur, actor_tmdb_id, actor_name, profile_url)
            character = member.get("character")
            order = member.get("order")
            ensure_movie_cast(cur, movie_id, actor_id, character, order)

        # 導演 (crew)
        for member in credits.get("crew", []):
            if member.get("job") == "Director":
                director_tmdb_id = member.get("id")
                director_actor_id = check_actor(cur, director_tmdb_id)
                if director_actor_id is None:
                    director_name = member.get("name")
                    profile_path = member.get("profile_path")
                    profile_url = f"{TMDB_IMG_BASE_URL}{profile_path}" if profile_path else None
                    director_actor_id = upsert_actor(cur, director_tmdb_id, director_name, profile_url)
                ensure_director(cur, movie_id, director_actor_id)

        conn.commit()
        return movie_id
        
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def store_actor(tmdb_actor_id, actor_data):
    """
    將 TMDB 演員資料存入資料庫（由外部傳入已解析資料）
    
    Args:
        tmdb_actor_id: TMDB 演員 ID
        actor_data: dict，包含以下欄位：
            - name: 演員姓名
            - profile_path: 頭像路徑
            - birthday: 生日（YYYY-MM-DD）
            - place_of_birth: 出生地
    
    Returns:
        actor_id: 資料庫中的演員 ID
    """
    conn = connect_db()
    cur = conn.cursor()

    actor_id = check_actor(cur, tmdb_actor_id)
    if check_actor_detail(cur, actor_id):
        print(f"Actor with tmdb_id {tmdb_actor_id} already exists, skipping.")
        cur.close()
        conn.close()
        return actor_id

    try:
        # 解析演員資訊
        name = actor_data.get("name")
        profile_path = actor_data.get("profile_path")
        profile_url = f"{TMDB_IMG_BASE_URL}{profile_path}" if profile_path else None
        birthdate = actor_data.get("birthday")  # 格式如 "1974-10-28"
        country = actor_data.get("place_of_birth")  # 字串，如 "Los Angeles, California, USA"
        
        # 儲存演員詳細資訊
        actor_id = upsert_actor_detail(cur, tmdb_actor_id, name, profile_url, birthdate, country)
        print("Note: Only basic actor information has been stored. No movie associations have been made.")
        
        conn.commit()
        return actor_id
        
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def get_movie_basic(cur, movie_id):
    cur.execute("SELECT movie_id, title, release_year, genre, rating, poster_url FROM MOVIE WHERE movie_id=%s", (movie_id,))
    return cur.fetchone()

def get_actor_basic(cur, actor_id):
    cur.execute("SELECT actor_id, name, birthdate, country, profile_url FROM ACTOR WHERE actor_id=%s", (actor_id,))
    return cur.fetchone()

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