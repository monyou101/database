"""
監控 /movies/<id> 端點的實際載入時間
"""

import time
from functools import wraps
from flask import g, request

def time_endpoint(f):
    """計時裝飾器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.start_time = time.time()
        result = f(*args, **kwargs)
        elapsed = time.time() - g.start_time
        print(f"[PERF] {f.__name__}({args}, {kwargs}): {elapsed:.3f}s")
        return result
    return decorated_function

def install_perf_monitoring(app):
    """為所有路由安裝效能監控"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            elapsed = time.time() - g.start_time
            # 只記錄重要的路由
            if request.path.startswith('/movies/') or request.path.startswith('/actors/'):
                print(f"[PERF] {request.method} {request.path}: {elapsed:.3f}s (status: {response.status_code})")
        return response
