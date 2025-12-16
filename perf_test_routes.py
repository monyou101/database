"""
Railway 效能測試端點
在 Flask 應用中新增用於測試的端點
"""
import time
from flask import jsonify

def register_perf_routes(app):
    """註冊效能測試路由"""
    
    @app.route('/api/perf/db-latency', methods=['GET'])
    def perf_db_latency():
        """測試資料庫查詢延遲"""
        from database import connect_db
        
        results = {
            'queries': [],
            'total_time': 0
        }
        
        try:
            conn = connect_db()
            cur = conn.cursor()
            
            # 查詢 1: 簡單計數
            start = time.time()
            cur.execute('SELECT COUNT(*) FROM MOVIE')
            r1 = cur.fetchone()
            t1 = time.time() - start
            results['queries'].append({
                'name': 'COUNT(*) FROM MOVIE',
                'time': f'{t1:.3f}s',
                'rows': r1[0]
            })
            
            # 查詢 2: 單一電影
            start = time.time()
            cur.execute('SELECT * FROM MOVIE WHERE movie_id = 281')
            r2 = cur.fetchone()
            t2 = time.time() - start
            results['queries'].append({
                'name': 'SELECT * FROM MOVIE WHERE movie_id=281',
                'time': f'{t2:.3f}s',
                'found': r2 is not None
            })
            
            # 查詢 3: 演員 JOIN
            start = time.time()
            cur.execute("""SELECT COUNT(*) FROM ACTOR a 
                JOIN MOVIE_CAST mc ON a.actor_id = mc.actor_id 
                WHERE mc.movie_id = 281""")
            r3 = cur.fetchone()
            t3 = time.time() - start
            results['queries'].append({
                'name': 'ACTORS JOIN for movie 281',
                'time': f'{t3:.3f}s',
                'count': r3[0]
            })
            
            # 查詢 4: 完整 get_movie_detail 流程
            start = time.time()
            cur.execute('SELECT * FROM MOVIE WHERE movie_id = 281')
            cur.fetchone()
            cur.execute("""SELECT a.actor_id, a.name FROM ACTOR a 
                JOIN MOVIE_CAST mc ON a.actor_id = mc.actor_id 
                WHERE mc.movie_id = 281 ORDER BY mc.billing_order""")
            cur.fetchall()
            cur.execute("""SELECT a.actor_id, a.name FROM ACTOR a 
                JOIN DIRECTOR d ON a.actor_id = d.actor_id 
                WHERE d.movie_id = 281""")
            cur.fetchall()
            cur.execute("""SELECT r.review_id FROM REVIEW r 
                JOIN USER u ON r.user_id = u.user_id 
                WHERE r.target_type = 'MOVIE' AND r.target_id = 281""")
            cur.fetchall()
            t4 = time.time() - start
            results['queries'].append({
                'name': 'Complete get_movie_detail (4 queries)',
                'time': f'{t4:.3f}s'
            })
            
            total = t1 + t2 + t3 + t4
            results['total_time'] = f'{total:.3f}s'
            results['analysis'] = {
                'connection_latency': 'Low' if total < 1 else 'High',
                'recommendation': 'OK' if total < 1 else 'Investigate connection pool or add caching'
            }
            
            cur.close()
            conn.close()
            
            return jsonify(results), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/perf/full-request/<int:movie_id>', methods=['GET'])
    def perf_full_request(movie_id):
        """測試完整的 /movies/<id> 端點時間"""
        from database import get_tmdb_id_from_movie_id, get_movie_detail, check_movie_detail
        
        timings = {}
        
        try:
            # 步驟 1: get_tmdb_id_from_movie_id
            start = time.time()
            tmdb_id = get_tmdb_id_from_movie_id(movie_id)
            timings['get_tmdb_id'] = f'{(time.time() - start):.3f}s'
            
            # 步驟 2: check_movie_detail
            start = time.time()
            check_result = check_movie_detail(movie_id)
            timings['check_movie_detail'] = f'{(time.time() - start):.3f}s'
            
            # 步驟 3: get_movie_detail
            start = time.time()
            movie = get_movie_detail(movie_id)
            timings['get_movie_detail'] = f'{(time.time() - start):.3f}s'
            
            if not movie:
                return jsonify({'error': 'Movie not found'}), 404
            
            return jsonify({
                'movie_id': movie_id,
                'tmdb_id': tmdb_id,
                'check_result': check_result,
                'timings': timings,
                'movie_title': movie.get('title'),
                'actors_count': len(movie.get('actors', [])),
                'directors_count': len(movie.get('directors', [])),
                'reviews_count': len(movie.get('reviews', []))
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
