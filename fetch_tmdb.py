# fetch_tmdb.py - CLI 操作和主要邏輯
import os
import sys
from database import fetch_and_store_movie, fetch_and_store_actor
from tmdb_api import fetch_popular_movies, fetch_tmdb_data

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fetch_tmdb.py <tmdb_movie_id> [tmdb_movie_id ...]")
        print("  python fetch_tmdb.py popular [pages]")
        print("  python fetch_tmdb.py search movie <query>")
        print("  python fetch_tmdb.py search actor <query>")
        sys.exit(1)

    if not os.getenv("TMDB_API_KEY"):
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