# tmdb_api.py - TMDB API 操作
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise EnvironmentError(
        "TMDB_API_KEY environment variable is not set. Please set it to your TMDB API key."
    )
TMDB_BASE_URL = "https://api.themoviedb.org/3"

_session = requests.Session()
_retries = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=("GET",),
)
_adapter = HTTPAdapter(max_retries=_retries, pool_connections=10, pool_maxsize=20)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)

def fetch_tmdb_data(url, params=None):
    request_params = {"api_key": TMDB_API_KEY, "language": "zh-TW"}
    if params:
        request_params.update(params)
    response = _session.get(f"{TMDB_BASE_URL}{url}", params=request_params, timeout=(3, 10))
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise requests.exceptions.HTTPError(
            f"HTTP error for TMDB endpoint '{url}' with params {request_params}: {e}"
        ) from e
    return response.json()

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