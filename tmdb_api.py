# tmdb_api.py - TMDB API 操作
import os
import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise EnvironmentError(
        "TMDB_API_KEY environment variable is not set. Please set it to your TMDB API key."
    )
TMDB_BASE_URL = "https://api.themoviedb.org/3"

def fetch_tmdb_data(url, params=None):
    request_params = {"api_key": TMDB_API_KEY, "language": "zh-TW"}
    if params:
        request_params.update(params)
    response = requests.get(f"{TMDB_BASE_URL}{url}", params=request_params, timeout=10)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise requests.exceptions.HTTPError(
            f"HTTP error for TMDB endpoint '{url}' with params {request_params}: {e}"
        ) from e
    return response.json()

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