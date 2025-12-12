from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_compress import Compress  # 新增壓縮
import os
import concurrent.futures  # 新增並發
from database import connect_db, fetch_and_store_movie, get_movie_id_from_tmdb_id
from tmdb_api import fetch_tmdb_data

app = Flask(__name__, static_folder='Movie_UI', static_url_path='')
app.secret_key = 'your_secret_key'  # 生產環境使用強密鑰
CORS(app)  # 允許前端跨域請求
Compress(app)  # 自動壓縮 JSON 回應

# 用戶認證 API（匹配 UI 登入/註冊功能）
@app.route('/auth/register', methods=['POST'])
def register():
    """用戶註冊"""
    data = request.json
    # username = data.get('username')
    email = data.get('email')
    password = data.get('password')  # 實際應 hash，例如使用 bcrypt
    
    if not all([email, password]):
        return jsonify({'error': 'Missing fields'}), 400
    
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO USER (username, email, password_hash) VALUES (%s, %s, %s)", (email, email, password))
        conn.commit()
        return jsonify({'success': True, 'message': 'User registered successfully'}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
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
        session['user_id'] = user['user_id']
        session['username'] = user['username']
        return jsonify({'success': True, 'token': 'dummy_token', 'user_email': email})
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/auth/logout', methods=['POST'])
def logout():
    """用戶登出"""
    session.clear()
    return jsonify({'message': 'Logged out'})

# 調整現有 API 以匹配 UI
@app.route('/movies', methods=['GET'])
def get_movies():
    """獲取電影清單（支援搜尋、分頁，匹配主頁清單）"""
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

# 新增端點：使用 tmdb_id 查詢電影詳細（若無，自動下載）
@app.route('/movies/tmdb/<int:tmdb_id>', methods=['GET'])
def get_movie_by_tmdb_id(tmdb_id):
    """使用 tmdb_id 獲取電影詳細（若資料庫無，自動從 TMDB 下載）"""
    movie_id = get_movie_id_from_tmdb_id(tmdb_id)
    if movie_id:
        # 資料庫有，直接呼叫現有 get_movie_detail
        return get_movie_detail(movie_id)
    else:
        # 資料庫無，自動下載
        try:
            fetch_and_store_movie(tmdb_id)
            # 下載後重新獲取 movie_id
            movie_id = get_movie_id_from_tmdb_id(tmdb_id)
            if movie_id:
                return get_movie_detail(movie_id)
            else:
                return jsonify({'error': 'Failed to retrieve movie after TMDB fetch'}), 500
        except Exception as e:
            return jsonify({'error': f'Failed to fetch movie from TMDB: {e}'}), 500

@app.route('/movies/<int:movie_id>', methods=['GET'])
def get_movie_detail(movie_id):
    """獲取電影詳細資訊（匹配 Movie.html 詳細頁）"""
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    # 電影基本資訊
    cur.execute("SELECT * FROM MOVIE WHERE movie_id = %s", (movie_id,))
    movie = cur.fetchone()
    if not movie:
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
    """獲取演員清單（支援搜尋，分頁，若 UI 有演員頁）"""
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
    """獲取演員詳細資訊（若 UI 有演員詳細頁）"""
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    
    # 演員基本資訊
    cur.execute("SELECT * FROM ACTOR WHERE actor_id = %s", (actor_id,))
    actor = cur.fetchone()
    if not actor:
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

@app.route('/reviews', methods=['POST'])
def add_review():
    """新增評論（需登入，匹配 UI 評論功能）"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    target_type = data.get('target_type')  # 'MOVIE', 'ACTOR' 等
    target_id = data.get('target_id')
    rating = data.get('rating')
    title = data.get('title')
    body = data.get('body')
    
    if not all([target_type, target_id, rating]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO REVIEW (user_id, target_type, target_id, rating, title, body)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session['user_id'], target_type, target_id, rating, title, body))
        conn.commit()
        return jsonify({'message': 'Review added successfully'}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/popular', methods=['GET'])
def get_popular_movies():
    """獲取熱門電影（匹配主頁熱門清單）"""
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
    def fetch_single(url, params):
        return fetch_tmdb_data(url, params)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(fetch_single, url, params) for url, params in urls_params]
        # 保持結果順序，初始化為 None
        results = [None] * len(futures)
        for idx, future in enumerate(futures):
            try:
                results[idx] = future.result()
            except Exception as e:
                results[idx] = {'error': str(e)}
    return results

@app.route('/api/search/movie', methods=['GET'])
def search_movie():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing query'}), 400
    data = fetch_tmdb_data('/search/movie', {'query': query})
    return jsonify(data)

@app.route('/api/search/person', methods=['GET'])
def search_person():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing query'}), 400
    data = fetch_tmdb_data('/search/person', {'query': query})
    return jsonify(data)

@app.route('/api/search/all', methods=['GET'])
def search_all():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing query'}), 400
    
    urls_params = [
        ('/search/movie', {'query': query}),
        ('/search/person', {'query': query})
    ]
    results = fetch_tmdb_concurrent(urls_params)
    return jsonify({
        'movie': results[0],
        'person': results[1]
    })

@app.route('/api/trending/movie/<path:time_window>', methods=['GET'])
def trending_movie(time_window):
    if time_window not in ['day', 'week']:
        return jsonify({'error': 'Invalid time_window'}), 400
    data = fetch_tmdb_data(f'/trending/movie/{time_window}')
    return jsonify(data)

@app.route('/api/movie/<path:endpoint>', methods=['GET'])
def movie_endpoint(endpoint):
    if endpoint not in ['now_playing', 'upcoming']:
        return jsonify({'error': 'Invalid endpoint'}), 400
    params = {'region': 'TW'}
    data = fetch_tmdb_data(f'/movie/{endpoint}', params)
    return jsonify(data)

@app.route('/api/trending/all', methods=['GET'])
def trending_all():
    urls_params = [
        ('/trending/movie/day', {}),
        ('/trending/movie/week', {}),
        ('/movie/now_playing', {'region': 'TW'}),
        ('/movie/upcoming', {'region': 'TW'})
    ]
    results = fetch_tmdb_concurrent(urls_params)
    return jsonify({
        'day': results[0],
        'week': results[1],
        'now_playing': results[2],
        'upcoming': results[3]
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))