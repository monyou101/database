import os
import requests
import mysql.connector

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

MAX_CAST_MEMBERS = 10

def fetch_tmdb_data(url, params=None):
    request_params = {"api_key": TMDB_API_KEY, "language": "zh-TW"}
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
        INSERT INTO `MOVIE` (tmdb_id, title, release_year, genre, runtime, overview, rating, poster_url)
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
        if row:
            return True
    return False

def upsert_actor(cur, tmdb_id, name, profile_url=None):
    cur.execute("""
        INSERT INTO `ACTOR` (tmdb_id, name, profile_url)
        VALUES (%s,%s,%s)
        ON DUPLICATE KEY UPDATE name=VALUES(name), profile_url=VALUES(profile_url)
    """, (tmdb_id, name, profile_url))
    cur.execute("SELECT actor_id FROM ACTOR WHERE tmdb_id=%s", (tmdb_id,))
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Failed to fetch actor_id for tmdb_id={tmdb_id}")
    print(f"Stored actor {name} (actor_id={row[0]})")
    return row[0]

def upsert_actor_detail(cur, tmdb_id, name, profile_url=None, birthdate=None, country=None):
    cur.execute("""
        INSERT INTO `ACTOR` (tmdb_id, name, profile_url, birthdate, country)
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
        INSERT IGNORE INTO `MOVIE_CAST` (movie_id, actor_id, character_name, billing_order)
        VALUES (%s,%s,%s,%s)
    """, (movie_id, actor_id, character_name, billing_order))

def ensure_director(cur, movie_id, actor_id):
    cur.execute("""
        INSERT IGNORE INTO `DIRECTOR` (movie_id, actor_id)
        VALUES (%s,%s)
    """, (movie_id, actor_id))

def fetch_person_details(person_tmdb_id):
    # 從 TMDB 獲取 person 的 birthday 與 place_of_birth
    try:
        data = fetch_tmdb_data(f"/person/{person_tmdb_id}")
        birthdate = data.get("birthday")  # 格式如 "1974-10-28"
        country = data.get("place_of_birth")  # 字串，如 "Los Angeles, California, USA"
        return birthdate, country
    except Exception as e:
        print(f"Warning: Failed to fetch details for person {person_tmdb_id}: {e}")
        return None, None

def fetch_and_store_movie(tmdb_movie_id):
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
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

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
                profile_url = f"https://image.tmdb.org/t/p/w500{profile_path}" if profile_path else None
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
                    profile_url = f"https://image.tmdb.org/t/p/w500{profile_path}" if profile_path else None
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
        profile_url = f"https://image.tmdb.org/t/p/w500{profile_path}" if profile_path else None
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

def fetch_popular_movies(pages=1):
    """回傳 popular 清單中的 movie ids"""
    try:
        pages_int = int(pages)
        if pages_int < 1:
            pages_int = 1
    except (ValueError, TypeError):
        raise ValueError(f"Invalid value for pages: {pages!r}. Must be an integer >= 1.")
    ids = []
    for p in range(1, pages_int + 1):
        data = fetch_tmdb_data("/movie/popular", params={"page": p})
        for item in data.get("results", []):
            mid = item.get("id")
            if isinstance(mid, int):
                ids.append(mid)
            else:
                print(f"Warning: Skipping non-integer movie ID {mid!r} (type: {type(mid).__name__}) from TMDB API response on page {p}")
    return ids

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fetch_tmdb.py <tmdb_movie_id> [tmdb_movie_id ...]")
        print("  python fetch_tmdb.py popular [pages]")
        print("  python fetch_tmdb.py search movie <query>")
        print("  python fetch_tmdb.py search actor <query>")
        sys.exit(1)

    if not TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY env var not set")

    # 支援兩種模式：單一/多 id，或 popular 批次抓取
    if sys.argv[1].lower() == "popular":
        pages = 1
        if len(sys.argv) >= 3:
            try:
                pages = int(sys.argv[2])
            except ValueError:
                print(f"Invalid pages value '{sys.argv[2]}', default to 1")
                pages = 1

        ids = fetch_popular_movies(pages=pages)
        print(f"Fetched {len(ids)} popular movie ids (pages={pages})")
        for mid in ids:
            try:
                fetch_and_store_movie(int(mid))
            except Exception as e:
                print(f"Failed to fetch/store movie {mid}: {e}")
    elif sys.argv[1].lower() == "search":
        if len(sys.argv) < 4:
            print("Usage: python fetch_tmdb.py search <type> <query>")
            print("  <type>: movie or actor")
            print("  <query>: search query (e.g., 'Inception' or 'Leonardo DiCaprio')")
            sys.exit(1)
        
        search_type = sys.argv[2].lower()
        query = " ".join(sys.argv[3:])
        
        if search_type == "movie":
            data = fetch_tmdb_data("/search/movie", params={"query": query})
            results = data.get("results", [])
            if not results:
                print(f"No movies found for query '{query}'")
                sys.exit(1)
            print(f"Found {len(results)} movies:")
            for i, movie in enumerate(results):
                title = movie.get("title", "Unknown")
                year = movie.get("release_date", "")[:4] if movie.get("release_date") else "Unknown"
                print(f"{i+1}. {title} ({year})")
            try:
                choice = int(input(f"Enter the number of the movie to fetch (1-{len(results)}), or 0 to cancel: "))
                if choice == 0:
                    print("Cancelled.")
                    sys.exit(0)
                if 1 <= choice <= len(results):
                    movie = results[choice-1]
                    tmdb_id = movie.get("id")
                    title = movie.get("title")
                    print(f"Selected movie: {title} (ID: {tmdb_id})")
                    fetch_and_store_movie(tmdb_id)
                else:
                    print("Invalid choice.")
                    sys.exit(1)
            except ValueError:
                print("Invalid input. Please enter a number.")
                sys.exit(1)
        elif search_type == "actor":
            data = fetch_tmdb_data("/search/person", params={"query": query})
            results = data.get("results", [])
            if not results:
                print(f"No actors found for query '{query}'")
                sys.exit(1)
            print(f"Found {len(results)} actors:")
            for i, person in enumerate(results):
                name = person.get("name", "Unknown")
                known_for = person.get("known_for_department", "Unknown")
                print(f"{i+1}. {name} (Known for: {known_for})")
            try:
                choice = int(input(f"Enter the number of the actor to fetch (1-{len(results)}), or 0 to cancel: "))
                if choice == 0:
                    print("Cancelled.")
                    sys.exit(0)
                if 1 <= choice <= len(results):
                    person = results[choice-1]
                    tmdb_id = person.get("id")
                    name = person.get("name")
                    print(f"Selected actor: {name} (ID: {tmdb_id})")
                    fetch_and_store_actor(tmdb_id)
                else:
                    print("Invalid choice.")
                    sys.exit(1)
            except ValueError:
                print("Invalid input. Please enter a number.")
                sys.exit(1)
        else:
            print(f"Invalid search type '{search_type}'. Use 'movie' or 'actor'.")
            sys.exit(1)
    else:
        for mid in sys.argv[1:]:
            try:
                fetch_and_store_movie(int(mid))
            except ValueError:
                print(f"Error: '{mid}' is not a valid integer movie ID. Skipping.")
            except Exception as e:
                print(f"Failed to fetch/store movie {mid}: {e}")
