from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_compress import Compress
import os
import concurrent.futures
import jwt
import datetime
import time
from threading import Lock
from database import (
    connect_db, 
    store_movie,
    store_actor,
    get_movie_id_from_tmdb_id,
    get_actor_id_from_tmdb_id,
    get_tmdb_id_from_actor_id,
    get_movie_basic,
    get_actor_basic,
    normalize_movie_row,
    normalize_actor_row
)
from tmdb_api import fetch_tmdb_data

app = Flask(__name__, static_folder='Movie_UI', static_url_path='')
CORS(app)
Compress(app)
SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key')
CACHE_TTL_SECONDS = 1800 # 30 分鐘 TTL
_cache = {}
_cache_lock = Lock()

def cache_get(key):
    with _cache_lock:
        item = _cache.get(key)
        if not item:
            return None
        if time.time() - item['ts'] > CACHE_TTL_SECONDS:
            _cache.pop(key, None)
            return None
        return item['data']

def cache_set(key, data):
    with _cache_lock:
        _cache[key] = {'ts': time.time(), 'data': data}

_seen_tmdb_movies = set()
_seen_tmdb_persons = set()
_seen_lock = Lock()

def mark_seen_movie(tmdb_id):
    with _seen_lock:
        _seen_tmdb_movies.add(tmdb_id)

def is_seen_movie(tmdb_id):
    with _seen_lock:
        return tmdb_id in _seen_tmdb_movies

def mark_seen_person(tmdb_id):
    with _seen_lock:
        _seen_tmdb_persons.add(tmdb_id)

def is_seen_person(tmdb_id):
    with _seen_lock:
        return tmdb_id in _seen_tmdb_persons

def reset_seen_sets():
    with _seen_lock:
        _seen_tmdb_movies.clear()
        _seen_tmdb_persons.clear()

def fetch_and_store_movie(tmdb_movie_id):
    """從 TMDB 獲取電影資料並存入資料庫"""
    movie_data = fetch_tmdb_data(f"/movie/{tmdb_movie_id}", params={"append_to_response": "credits,genres"})
    return store_movie(tmdb_movie_id, movie_data)

def fetch_and_store_actor(tmdb_actor_id):
    """從 TMDB 獲取演員資料並存入資料庫"""
    actor_data = fetch_tmdb_data(f"/person/{tmdb_actor_id}")
    return store_actor(tmdb_actor_id, actor_data)

@app.route('/auth/register', methods=['POST'])
def register():
    """用戶註冊"""
    data = request.json
    # username = data.get('username')
    email = data.get('email')
    password = data.get('password')  # 實際應 hash，例如使用 bcrypt
    
    if not all([email, password]):
        return jsonify({'success': False, 'message': 'Missing fields'}), 400
    
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO USER (username, email, password_hash) VALUES (%s, %s, %s)", (email, email, password))
        conn.commit()
        return jsonify({'success': True, 'message': 'User registered successfully'}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/auth/login', methods=['POST'])
def login():
    """用戶登入"""
    data = request.json
    # username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_id, username FROM USER WHERE email = %s AND password_hash = %s", (email, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user:
        payload = {
            'user_id': user['user_id'],
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'success': True,
            'token': token,
            'user_email': email
        })
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/auth/logout', methods=['POST'])
def logout():
    """用戶登出"""
    return jsonify({'message': 'Logged out'})

@app.route('/movies', methods=['GET'])
def get_movies():
    """獲取電影清單"""
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    offset = (page - 1) * limit
    
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    sql = """
        SELECT movie_id, title, release_year, genre, rating, poster_url
        FROM MOVIE
        WHERE title LIKE %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """
    cur.execute(sql, (f'%{query}%', limit, offset))
    movies = cur.fetchall()
    
    cur.close()
    conn.close()
    return jsonify(movies)

@app.route('/movies/<int:movie_id>', methods=['GET'])
def get_movie_detail(movie_id):
    """獲取電影詳細資訊"""
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    # 電影基本資訊
    cur.execute("SELECT * FROM MOVIE WHERE movie_id = %s", (movie_id,))
    movie = cur.fetchone()
    if not movie:
        cur.close()
        conn.close()
        return jsonify({'error': 'Movie not found'}), 404
    
    # 演員
    cur.execute("""
        SELECT a.actor_id, a.name, a.birthdate, a.country, a.profile_url, mc.character_name, mc.billing_order
        FROM ACTOR a
        JOIN MOVIE_CAST mc ON a.actor_id = mc.actor_id
        WHERE mc.movie_id = %s
        ORDER BY mc.billing_order
    """, (movie_id,))
    actors = cur.fetchall()
    
    # 導演
    cur.execute("""
        SELECT a.actor_id, a.name, a.birthdate, a.country, a.profile_url
        FROM ACTOR a
        JOIN DIRECTOR d ON a.actor_id = d.actor_id
        WHERE d.movie_id = %s
    """, (movie_id,))
    directors = cur.fetchall()
    
    # 評論
    cur.execute("""
        SELECT r.review_id, r.rating, r.title, r.body, r.created_at, u.username
        FROM REVIEW r
        JOIN USER u ON r.user_id = u.user_id
        WHERE r.target_type = 'MOVIE' AND r.target_id = %s
        ORDER BY r.created_at DESC
    """, (movie_id,))
    reviews = cur.fetchall()
    
    cur.close()
    conn.close()
    
    movie['actors'] = actors
    movie['directors'] = directors
    movie['reviews'] = reviews
    return jsonify(movie)

@app.route('/actors', methods=['GET'])
def get_actors():
    """獲取演員清單"""
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    offset = (page - 1) * limit
    
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    sql = """
        SELECT actor_id, name, birthdate, country, profile_url
        FROM ACTOR
        WHERE name LIKE %s
        ORDER BY name
        LIMIT %s OFFSET %s
    """
    cur.execute(sql, (f'%{query}%', limit, offset))
    actors = cur.fetchall()
    
    cur.close()
    conn.close()
    return jsonify(actors)

@app.route('/actors/<int:actor_id>', methods=['GET'])
def get_actor_detail(actor_id):
    """獲取演員詳細資訊"""
    tmdb_id = get_tmdb_id_from_actor_id(actor_id)
    if tmdb_id:
        fetch_and_store_actor(tmdb_id)
    
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    # 演員基本資訊
    cur.execute("SELECT * FROM ACTOR WHERE actor_id = %s", (actor_id,))
    actor = cur.fetchone()
    if not actor:
        cur.close()
        conn.close()
        return jsonify({'error': 'Actor not found'}), 404
    
    # 參與電影（作為演員）
    cur.execute("""
        SELECT m.movie_id, m.title, m.release_year, m.genre, m.rating, m.poster_url, mc.character_name
        FROM MOVIE m
        JOIN MOVIE_CAST mc ON m.movie_id = mc.movie_id
        WHERE mc.actor_id = %s
        ORDER BY m.release_year DESC
    """, (actor_id,))
    movies_as_actor = cur.fetchall()
    
    # 參與電影（作為導演）
    cur.execute("""
        SELECT m.movie_id, m.title, m.release_year, m.genre, m.rating, m.poster_url
        FROM MOVIE m
        JOIN DIRECTOR d ON m.movie_id = d.movie_id
        WHERE d.actor_id = %s
        ORDER BY m.release_year DESC
    """, (actor_id,))
    movies_as_director = cur.fetchall()
    
    cur.close()
    conn.close()
    
    actor['movies_as_actor'] = movies_as_actor
    actor['movies_as_director'] = movies_as_director
    return jsonify(actor)

@app.route('/reviews/add', methods=['POST'])
def add_review():
    """新增評論"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'message': 'Missing or invalid token'}), 401
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['user_id']
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'error': 'Invalid token'}), 401
    
    data = request.json
    target_type = data.get('target_type')
    target_id = data.get('target_id')
    rating = data.get('rating', 5)
    title = data.get('title', '')
    body = data.get('body')
    
    if not all([target_type, target_id, rating]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO REVIEW (user_id, target_type, target_id, rating, title, body)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE rating=VALUES(rating), title=VALUES(title), body=VALUES(body)
        """, (user_id, target_type, target_id, rating, title, body))
        conn.commit()
        return jsonify({'success': True, 'message': 'Review added successfully'}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/reviews/<int:movie_id>', methods=['GET'])
def get_movie_review(movie_id):
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
    
    return jsonify({'reviews': reviews}), 200

@app.route('/popular', methods=['GET'])
def get_popular_movies():
    """獲取熱門電影"""
    limit = int(request.args.get('limit', 10))
    
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    cur.execute("""
        SELECT movie_id, title, release_year, genre, rating, poster_url
        FROM MOVIE
        ORDER BY rating DESC
        LIMIT %s
    """, (limit,))
    movies = cur.fetchall()
    
    cur.close()
    conn.close()
    return jsonify(movies)

def fetch_tmdb_concurrent(urls_params):
    """並發獲取 TMDB 資料（帶快取）"""
    import json
    
    def fetch_single(url, params):
        cache_key = f"tmdb:{url}:{json.dumps(params, sort_keys=True)}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached
        data = fetch_tmdb_data(url, params)
        cache_set(cache_key, data)
        return data
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(fetch_single, url, params) for url, params in urls_params]
        results = [None] * len(futures)
        for idx, future in enumerate(futures):
            try:
                results[idx] = future.result()
            except Exception as e:
                results[idx] = {'error': str(e)}
    return results

@app.route('/api/search/all', methods=['GET'])
def search_all():
    """搜尋電影與演員（回傳 DB id）"""
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing query'}), 400

    cache_key = f"search_all:{query}"
    cached = cache_get(cache_key)
    if cached:
        return jsonify(cached)
    
    urls_params = [
        ('/search/movie', {'query': query}),
        ('/search/person', {'query': query})
    ]
    results = fetch_tmdb_concurrent(urls_params)
    movie_block, person_block = results[0], results[1]

    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # 映射電影
        normalized_movies = []
        for m in movie_block.get('results', [])[:12] if isinstance(movie_block, dict) else []:
            tmdb_id = m.get('id')
            if not tmdb_id:
                continue
            
            if not is_seen_movie(tmdb_id):
                try:
                    # 傳入 TMDB 資料
                    store_movie(tmdb_id, m)
                    mark_seen_movie(tmdb_id)
                except Exception as e:
                    print(f"Warning: Failed to store movie {tmdb_id}: {e}")
                    continue
            
            movie_id = get_movie_id_from_tmdb_id(tmdb_id)
            if movie_id:
                row = get_movie_basic(cur, movie_id)
                nm = normalize_movie_row(row)
                if nm:
                    normalized_movies.append(nm)
        # 映射人物
        normalized_people = []
        for p in person_block.get('results', [])[:12] if isinstance(person_block, dict) else []:
            tmdb_pid = p.get('id')
            if not tmdb_pid:
                continue
            
            if not is_seen_person(tmdb_pid):
                try:
                    store_actor(tmdb_pid, p)
                    mark_seen_person(tmdb_pid)
                except Exception as e:
                    print(f"Warning: Failed to store actor {tmdb_pid}: {e}")
                    continue
            
            actor_id = get_actor_id_from_tmdb_id(tmdb_pid)
            if actor_id:
                row = get_actor_basic(cur, actor_id)
                na = normalize_actor_row(row)
                if na:
                    normalized_people.append(na)
        
        payload = {'movie': normalized_movies, 'person': normalized_people}
        cache_set(cache_key, payload)
        return jsonify(payload)
        
    finally:
        cur.close()
        conn.close()

@app.route('/api/trending/all', methods=['GET'])
def trending_all():
    """獲取所有 trending 資料"""
    cache_key = "trending_all"
    cached = cache_get(cache_key)
    if cached:
        return jsonify(cached)

    urls_params = [
        ('/trending/movie/day', {}),
        ('/trending/movie/week', {}),
        ('/movie/now_playing', {'region': 'TW'}),
        ('/movie/upcoming', {'region': 'TW'})
    ]
    results = fetch_tmdb_concurrent(urls_params)

    conn = connect_db()
    cur = conn.cursor(dictionary=True)

    try:
        normalized_blocks = []
        for block in results:
            normalized_movies = []
            for m in block.get('results', []) if isinstance(block, dict) else []:
                tmdb_id = m.get('id')
                if not tmdb_id:
                    continue
                
                if not is_seen_movie(tmdb_id):
                    try:
                        fetch_and_store_movie(tmdb_id)
                        mark_seen_movie(tmdb_id)
                    except Exception as e:
                        print(f"Warning: Failed to store movie {tmdb_id}: {e}")
                        continue
                
                movie_id = get_movie_id_from_tmdb_id(tmdb_id)
                if movie_id:
                    row = get_movie_basic(cur, movie_id)
                    nm = normalize_movie_row(row)
                    if nm:
                        normalized_movies.append(nm)
            
            normalized_blocks.append(normalized_movies)

        payload = {
            'day': normalized_blocks[0] if len(normalized_blocks) > 0 else [],
            'week': normalized_blocks[1] if len(normalized_blocks) > 1 else [],
            'now_playing': normalized_blocks[2] if len(normalized_blocks) > 2 else [],
            'upcoming': normalized_blocks[3] if len(normalized_blocks) > 3 else []
        }

        cache_set(cache_key, payload)
        reset_seen_sets()
        return jsonify(payload)
        
    finally:
        cur.close()
        conn.close()

@app.route('/api/cmd', methods=['POST'])
def cli_cmd():
    """執行 SQL 指令（僅限開發環境）"""
    data = request.json
    command = data.get('command', '').strip()
    
    if not command:
        return jsonify({'error': 'Empty command'}), 400
    
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        cur.execute(command)
        results = cur.fetchall()
        
        return jsonify({
            'success': True,
            'command': command,
            'rows': len(results),
            'data': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'command': command,
            'error': str(e)
        }), 400
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    pass