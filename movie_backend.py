from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_compress import Compress
import os
import concurrent.futures
import jwt
import datetime
import time
from threading import Lock
from database import (
    store_movie,
    store_actor,
    check_movie_detail,
    check_actor_detail,
    get_movie_id_from_tmdb_id,
    get_movies_by_tmdb_ids,
    get_tmdb_id_from_movie_id,
    get_actor_id_from_tmdb_id,
    get_actors_by_tmdb_ids,
    get_tmdb_id_from_actor_id,
    normalize_movie_row,
    normalize_actor_row,
    create_user,
    get_user_by_email,
    search_movies,
    get_movie_detail,
    search_actors,
    get_actor_detail,
    add_review,
    get_movie_reviews,
    execute_sql_query,
)
from tmdb_api import fetch_tmdb_data
from perf_test_routes import register_perf_routes
from perf_monitoring import install_perf_monitoring

app = Flask(__name__, static_folder='Movie_UI', static_url_path='')
CORS(app)
Compress(app)

# 安裝效能監控
install_perf_monitoring(app)

# 註冊效能測試端點
register_perf_routes(app)
SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key')
CACHE_TTL_SECONDS = 1800
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

def fetch_and_store_movie(movie_id, tmdb_movie_id):
    """從 TMDB 獲取電影資料並存入資料庫"""
    import time
    
    t_check = time.time()
    needs_fetch = (movie_id is None or check_movie_detail(movie_id) is False)
    print(f"[PERF-DETAIL]   check_movie_detail({movie_id}): {time.time()-t_check:.3f}s -> needs_fetch={needs_fetch}")
    
    if needs_fetch:
        try:
            t_fetch = time.time()
            movie_data = fetch_tmdb_data(f"/movie/{tmdb_movie_id}", params={"append_to_response": "credits,genres"})
            print(f"[PERF-DETAIL]   fetch_tmdb_data (TMDB API): {time.time()-t_fetch:.3f}s")
            
            t_store = time.time()
            result = store_movie(tmdb_movie_id, movie_data)
            print(f"[PERF-DETAIL]   store_movie: {time.time()-t_store:.3f}s")
            return result
        except Exception as e:
            print(f"Error fetching/storing movie {tmdb_movie_id}: {e}")
            raise
    else:
        return movie_id

def fetch_and_store_actor(actor_id, tmdb_actor_id):
    """從 TMDB 獲取演員資料並存入資料庫"""
    if actor_id is None or check_actor_detail(actor_id) is False:
        try:
            actor_data = fetch_tmdb_data(f"/person/{tmdb_actor_id}")
            return store_actor(tmdb_actor_id, actor_data)
        except Exception as e:
            print(f"Error fetching/storing actor {tmdb_actor_id}: {e}")
            raise
    else:
        return actor_id

@app.route('/auth/register', methods=['POST'])
def register():
    """用戶註冊"""
    data = request.json
    # username = data.get('username')
    email = data.get('email')
    password = data.get('password')  # 實際應 hash，例如使用 bcrypt
    
    if not all([email, password]):
        return jsonify({'success': False, 'message': 'Missing fields'}), 400
    
    try:
        create_user(email, password)
        return jsonify({'success': True, 'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """用戶登入"""
    data = request.json
    # username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    user = get_user_by_email(email, password)
    
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
    
    movies = search_movies(query, page, limit)
    return jsonify(movies)

@app.route('/movies/<int:movie_id>', methods=['GET'])
def get_movie_detail_route(movie_id):
    """獲取電影詳細資訊"""
    import time
    t_start = time.time()
    
    # 直接查詢，不做額外的 tmdb_id 或 check 查詢
    t1 = time.time()
    movie = get_movie_detail(movie_id)
    print(f"[PERF-DETAIL] get_movie_detail({movie_id}): {time.time()-t1:.3f}s")
    
    print(f"[PERF-DETAIL] TOTAL /movies/{movie_id}: {time.time()-t_start:.3f}s")
    
    if not movie:
        return jsonify({'error': 'Movie not found'}), 404
    return jsonify(movie)

@app.route('/actors', methods=['GET'])
def get_actors():
    """獲取演員清單"""
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    
    actors = search_actors(query, page, limit)
    return jsonify(actors)

@app.route('/actors/<int:actor_id>', methods=['GET'])
def get_actor_detail_route(actor_id):
    """獲取演員詳細資訊"""
    tmdb_id = get_tmdb_id_from_actor_id(actor_id)
    if tmdb_id is not None:
        fetch_and_store_actor(actor_id, tmdb_id)
    else:
        print(f"Warning: Failed to get actor_tmdb_id: {actor_id}")
    
    actor = get_actor_detail(actor_id)
    if not actor:
        return jsonify({'error': 'Actor not found'}), 404
    return jsonify(actor)

@app.route('/reviews/add', methods=['POST'])
def add_review_route():
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
    
    try:
        add_review(user_id, target_type, target_id, rating, title, body)
        return jsonify({'success': True, 'message': 'Review added successfully'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/reviews/<int:movie_id>', methods=['GET'])
def get_movie_review_route(movie_id):
    """獲取電影評論"""
    reviews = get_movie_reviews(movie_id)
    return jsonify({'reviews': reviews}), 200

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

    try:
        movie_tmdb_ids = [m.get('id') for m in movie_block.get('results', []) if m.get('id') and not is_seen_movie(m.get('id'))]
        actor_tmdb_ids = [p.get('id') for p in person_block.get('results', []) if p.get('id') and not is_seen_person(p.get('id'))]

        if movie_tmdb_ids:
            existing_movie_map = get_movies_by_tmdb_ids(movie_tmdb_ids)
            missing_movie_ids = [mid for mid in movie_tmdb_ids if mid not in existing_movie_map]
            for tmdb_id in missing_movie_ids:
                m = next((x for x in movie_block.get('results', []) if x.get('id') == tmdb_id), None)
                if m:
                    try:
                        store_movie(tmdb_id, m)
                    except Exception as e:
                        print(f"Warning: Failed to store movie {tmdb_id}: {e}")
                mark_seen_movie(tmdb_id)

        if actor_tmdb_ids:
            existing_actor_map = get_actors_by_tmdb_ids(actor_tmdb_ids)
            missing_actor_ids = [aid for aid in actor_tmdb_ids if aid not in existing_actor_map]
            for tmdb_id in missing_actor_ids:
                p = next((x for x in person_block.get('results', []) if x.get('id') == tmdb_id), None)
                if p:
                    try:
                        store_actor(tmdb_id, p)
                    except Exception as e:
                        print(f"Warning: Failed to store actor {tmdb_id}: {e}")
                mark_seen_person(tmdb_id)

        movie_map = get_movies_by_tmdb_ids([m.get('id') for m in movie_block.get('results', []) if m.get('id')])
        actor_map = get_actors_by_tmdb_ids([p.get('id') for p in person_block.get('results', []) if p.get('id')])
        
        normalized_movies = [normalize_movie_row(movie_map[mid]) for mid in movie_map if movie_map[mid]]
        normalized_people = [normalize_actor_row(actor_map[aid]) for aid in actor_map if actor_map[aid]]
        
        payload = {'movie': normalized_movies, 'person': normalized_people}
        cache_set(cache_key, payload)
        return jsonify(payload)
        
    except Exception as e:
        print(f"Error in search_all: {e}")
        return jsonify({'error': str(e)}), 500

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

    try:
        normalized_blocks = []
        for block in results:
            movie_results = block.get('results', []) if isinstance(block, dict) else []
            movie_tmdb_ids = [m.get('id') for m in movie_results if m.get('id')]

            if movie_tmdb_ids:
                existing_map = get_movies_by_tmdb_ids(movie_tmdb_ids)
                missing = [mid for mid in movie_tmdb_ids if mid not in existing_map]
                for tmdb_id in missing:
                    mark_seen_movie(tmdb_id)
                    m = next((x for x in movie_results if x.get('id') == tmdb_id), None)
                    if m:
                        try:
                            store_movie(tmdb_id, m)
                        except Exception as e:
                            print(f"Warning: Failed to store movie {tmdb_id}: {e}")

            movies_data = get_movies_by_tmdb_ids(movie_tmdb_ids) if movie_tmdb_ids else {}
            normalized_movies = [normalize_movie_row(m) for m in movies_data.values()]
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
        
    except Exception as e:
        print(f"Error in search_all: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cmd', methods=['POST'])
def cli_cmd():
    """執行 SQL 指令（僅限開發環境）"""
    data = request.json
    command = data.get('command', '').strip()
    
    if not command:
        return jsonify({'error': 'Empty command'}), 400
    
    try:
        results = execute_sql_query(command)
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

if __name__ == '__main__':
    pass