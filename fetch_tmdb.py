import os
import requests
import mysql.connector

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "eb1fb6b7c15b25a9d9784a0dd8b38681")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "myuser")
DB_PASS = os.getenv("DB_PASS", "myuser")
DB_NAME = os.getenv("DB_NAME", "mydb")

BASE_URL = "https://api.themoviedb.org/3"

def fetch_tmdb_data(url, params=None):
    request_params = {"api_key": TMDB_API_KEY}
    if params:
        request_params.update(params)
    response = requests.get(f"{BASE_URL}{url}", params=request_params, timeout=10)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise requests.exceptions.HTTPError(
            f"HTTP error for TMDB endpoint '{url}' with params {request_params}: {e}"
        ) from e
    return response.json()

def connect_db():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME, autocommit=False
    )

def upsert_movie(cur, tmdb_id, title, release_year, genre, rating):
    cur.execute("""
        INSERT INTO `MOVIE` (tmdb_id, title, release_year, genre, rating)
        VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
          title=VALUES(title), release_year=VALUES(release_year), genre=VALUES(genre), rating=VALUES(rating)
    """, (tmdb_id, title, release_year, genre, rating))
    # 回傳 movie_id
    cur.execute("SELECT movie_id FROM MOVIE WHERE tmdb_id=%s", (tmdb_id,))
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Failed to fetch movie_id for tmdb_id={tmdb_id}")
    return row[0]

def upsert_actor(cur, tmdb_id, name, birthdate=None, country=None):
    cur.execute("""
        INSERT INTO `ACTOR` (tmdb_id, name, birthdate, country)
        VALUES (%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE name=VALUES(name), birthdate=VALUES(birthdate), country=VALUES(country)
    """, (tmdb_id, name, birthdate, country))
    cur.execute("SELECT actor_id FROM ACTOR WHERE tmdb_id=%s", (tmdb_id,))
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Failed to fetch movie_id for tmdb_id={tmdb_id}")
    return row[0]

def ensure_movie_cast(cur, movie_id, actor_id, character_name, billing_order):
    # UNIQUE (movie_id, actor_id) 已存在時 INSERT IGNORE 可以跳過
    cur.execute("""
        INSERT IGNORE INTO `MOVIE_CAST` (movie_id, actor_id, character_name, billing_order)
        VALUES (%s,%s,%s,%s)
    """, (movie_id, actor_id, character_name, billing_order))

def ensure_director(cur, movie_id, actor_id):
    cur.execute("""
        INSERT IGNORE INTO `DIRECTOR` (movie_id, actor_id)
        VALUES (%s,%s)
    """, (movie_id, actor_id))

def fetch_and_store_movie(tmdb_movie_id):
    data = fetch_tmdb_data(f"/movie/{tmdb_movie_id}", params={"append_to_response":"credits,genres"})
    title = data.get("title")
    release_year = None
    if data.get("release_date"):
        release_year = data["release_date"].split("-")[0]
    genres = ", ".join([g["name"] for g in data.get("genres", [])]) if data.get("genres") else None
    rating = data.get("vote_average")

    conn = connect_db()
    cur = conn.cursor()

    try:
        movie_id = upsert_movie(cur, tmdb_movie_id, title, release_year, genres, rating)

        credits = data.get("credits", {})
        # actors (cast)
        for member in credits.get("cast", []):
            actor_tmdb_id = member.get("id")
            actor_name = member.get("name")
            character = member.get("character")
            order = member.get("order")
            # 不呼叫 actor detail 以降低 API 次數；若需出生地、生日可額外呼叫 /person/{id}
            actor_id = upsert_actor(cur, actor_tmdb_id, actor_name, None, None)
            ensure_movie_cast(cur, movie_id, actor_id, character, order)

        # crew -> director
        for member in credits.get("crew", []):
            if member.get("job") == "Director":
                director_tmdb_id = member.get("id")
                director_name = member.get("name")
                director_actor_id = upsert_actor(cur, director_tmdb_id, director_name, None, None)
                ensure_director(cur, movie_id, director_actor_id)

        conn.commit()
        print(f"Stored movie {title} (movie_id={movie_id})")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python fetch_tmdb.py <tmdb_movie_id> [tmdb_movie_id ...]")
        sys.exit(1)

    if not TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY env var not set")

    for mid in sys.argv[1:]:
        try:
            fetch_and_store_movie(int(mid))
        except ValueError:
            print(f"Error: '{mid}' is not a valid integer movie ID. Skipping.")
