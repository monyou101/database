# database.py - MySQL 資料庫操作
import os
import mysql.connector

TMDB_IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"

def connect_db():
    # 使用 Railway 的 MYSQL_URL 或個別變數
    mysql_url = os.getenv("MYSQL_URL")  # e.g., mysql://user:pass@host:port/db
    if mysql_url:
        # 解析 URL（或用 mysql.connector 直接解析）
        return mysql.connector.connect(
            host=os.getenv("MYSQLHOST"),
            database=os.getenv("MYSQLDATABASE"),
            user=os.getenv("MYSQLUSER"),
            password=os.getenv("MYSQLPASSWORD"),
            port=os.getenv("MYSQLPORT", 3306)
        )
    else:
        # 備用：個別變數
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "myuser"),
            password=os.getenv("DB_PASS", "myuser"),
            database=os.getenv("DB_NAME", "mydb")
        )

def check_movie(cur, tmdb_id):
    # 先檢查是否存在，避免重複插入時消耗 AUTO_INCREMENT
    cur.execute("SELECT movie_id FROM MOVIE WHERE tmdb_id=%s", (tmdb_id,))
    row = cur.fetchone()
    if row:
        return row[0]  # 已存在，直接回傳 movie_id
    return None  # 明確返回 None 若不存在

def upsert_movie(cur, tmdb_id, title, release_year, genre, runtime, overview, rating, poster_url=None):
    cur.execute("""
        INSERT INTO MOVIE (tmdb_id, title, release_year, genre, runtime, overview, rating, poster_url)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
          title=VALUES(title), release_year=VALUES(release_year), genre=VALUES(genre), runtime=VALUES(runtime), overview=VALUES(overview), rating=VALUES(rating), poster_url=VALUES(poster_url)
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
        ON DUPLICATE KEY UPDATE name=VALUES(name), profile_url=VALUES(profile_url)
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
        ON DUPLICATE KEY UPDATE name=VALUES(name), profile_url=VALUES(profile_url), birthdate=VALUES(birthdate), country=VALUES(country)
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

def fetch_and_store_movie(tmdb_movie_id):
    from tmdb_api import fetch_tmdb_data
    conn = connect_db()
    cur = conn.cursor()

    if check_movie(cur, tmdb_movie_id):
        print(f"Movie with tmdb_id {tmdb_movie_id} already exists, skipping.")
        cur.close()
        conn.close()
        return

    data = fetch_tmdb_data(f"/movie/{tmdb_movie_id}", params={"append_to_response":"credits,genres"})
    title = data.get("title")
    release_year = None
    if data.get("release_date"):
        release_year = data["release_date"].split("-")[0]
    genres = ", ".join([g["name"] for g in data.get("genres", [])]) if data.get("genres") else None
    runtime = data.get("runtime")
    overview = data.get("overview")
    rating = data.get("vote_average")
    poster_path = data.get("poster_path")
    poster_url = f"{TMDB_IMG_BASE_URL}{poster_path}" if poster_path else None

    try:
        movie_id = upsert_movie(cur, tmdb_movie_id, title, release_year, genres, runtime, overview, rating, poster_url)

        credits = data.get("credits", {})
        # actors (cast)
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

        # crew -> director
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
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def fetch_and_store_actor(tmdb_actor_id):
    from tmdb_api import fetch_tmdb_data, fetch_person_details
    conn = connect_db()
    cur = conn.cursor()

    actor_id = check_actor(cur, tmdb_actor_id)
    if check_actor_detail(cur, actor_id):
        print(f"Actor with tmdb_id {tmdb_actor_id} already exists, skipping.")
        cur.close()
        conn.close()
        return

    try:
        data = fetch_tmdb_data(f"/person/{tmdb_actor_id}")
        name = data.get("name")
        profile_path = data.get("profile_path")
        profile_url = f"{TMDB_IMG_BASE_URL}{profile_path}" if profile_path else None
        birthdate, country = fetch_person_details(tmdb_actor_id)
        upsert_actor_detail(cur, tmdb_actor_id, name, profile_url, birthdate, country)
        print("Note: Only basic actor information has been stored. No movie associations have been made." \
        " To associate this actor with movies, please use the appropriate functionality separately.")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()