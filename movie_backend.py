from flask import Flask, request, jsonify, session
from flask_cors import CORS
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 生產環境使用強密鑰
CORS(app)  # 允許前端跨域請求

# 資料庫連線設定（從環境變數讀取）
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "myuser")
DB_PASS = os.getenv("DB_PASS", "myuser")
DB_NAME = os.getenv("DB_NAME", "mydb")

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
    )

# 用戶認證 API（匹配 UI 登入/註冊功能）
@app.route('/register', methods=['POST'])
def register():
    """用戶註冊"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')  # 實際應 hash，例如使用 bcrypt
    
    if not all([username, email, password]):
        return jsonify({'error': 'Missing fields'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO USER (username, email, password_hash) VALUES (%s, %s, %s)", (username, email, password))
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    """用戶登入"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_id, username FROM USER WHERE username = %s AND password_hash = %s", (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user:
        session['user_id'] = user['user_id']
        session['username'] = user['username']
        return jsonify({'user_id': user['user_id'], 'username': user['username']})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
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
    
    conn = get_db_connection()
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
    """獲取電影詳細資訊（匹配 Movie.html 詳細頁）"""
    conn = get_db_connection()
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
    
    conn = get_db_connection()
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
    conn = get_db_connection()
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
    
    conn = get_db_connection()
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
    
    conn = get_db_connection()
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

if __name__ == '__main__':
    app.run(debug=True)