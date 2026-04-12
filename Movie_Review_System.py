# TMDb Smart Movie Explorer - Updated Version
import sqlite3
import requests
from colorama import Fore, init
import time

init(autoreset=True)

TMDB_API_KEY = "88121fd4207a0d0d1d5da3ce591d5cf4"  # Replace with your new TMDb API key

# Connect SQLite DB
conn = sqlite3.connect("tmdb_movies.db")
cursor = conn.cursor()

# Create Movies Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY,
    title TEXT,
    genre TEXT,
    release_date TEXT,
    budget REAL,
    revenue REAL,
    rating REAL,
    overview TEXT,
    country TEXT,
    director TEXT
)
""")
conn.commit()

# Fetch movie details from TMDb
def fetch_movie_details(movie_title):
    url_search = f"https://api.themoviedb.org/3/search/movie?query={movie_title}&api_key={TMDB_API_KEY}"
    try:
        res = requests.get(url_search, timeout=10).json()
    except:
        print(Fore.RED + "⚠️ TMDb request failed!")
        return None
    results = res.get("results")
    if not results:
        return None
    movie = results[0]
    movie_id = movie["id"]

    details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits"
    try:
        det = requests.get(details_url, timeout=10).json()
    except:
        print(Fore.RED + f"⚠️ Failed fetching details for {movie_title}")
        return None

    director = "Unknown"
    for person in det.get("credits", {}).get("crew", []):
        if person.get("job") == "Director":
            director = person.get("name")
            break

    genres = ", ".join([g["name"] for g in det.get("genres", [])])
    release_date = det.get("release_date", "Unknown")
    budget = det.get("budget")
    revenue = det.get("revenue")
    budget_value = budget if budget else None
    revenue_value = revenue if revenue else None
    rating = det.get("vote_average", 0)
    overview = det.get("overview", "")
    country = det.get("production_countries")[0]["iso_3166_1"] if det.get("production_countries") else "Unknown"

    return {
        "movie_id": movie_id,
        "title": det.get("title", "Unknown"),
        "genre": genres,
        "release_date": release_date,
        "budget": budget,
        "revenue": revenue,
        "rating": rating,
        "overview": overview,
        "country": country,
        "director": director
    }

# Add movie to DB
def add_movie_to_db(data):
    cursor.execute("""
        INSERT OR IGNORE INTO movies (movie_id, title, genre, release_date, budget, revenue, rating, overview, country, director)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["movie_id"], data["title"], data["genre"], data["release_date"],
        data["budget"], data["revenue"], data["rating"], data["overview"],
        data["country"], data["director"]
    ))
    conn.commit()

# Auto-fetch movies from TMDb (top popular movies)
def auto_fetch_movies(total_pages=10):
    print(Fore.CYAN + "📥 Fetching movies from TMDb...\n")

    for page in range(1, total_pages + 1):
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&page={page}"
        try:
            response = requests.get(url, timeout=10).json()
        except:
            print(Fore.RED + f"⚠️ Failed fetching page {page}")
            continue

        movies = response.get("results", [])
        print(Fore.YELLOW + f"Fetching Page {page}... ({len(movies)} movies)")

        for m in movies:
            movie_id = m["id"]
            details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits"
            try:
                details = requests.get(details_url, timeout=10).json()
            except:
                print(Fore.RED + f"⚠️ Failed fetching details for {movie_id}")
                continue

            director = "Unknown"
            for person in details.get("credits", {}).get("crew", []):
                if person.get("job") == "Director":
                    director = person.get("name")
                    break

            genres = ", ".join([g["name"] for g in details.get("genres", [])])
            release_date = details.get("release_date", "Unknown")
            budget = details.get("budget", 0)
            revenue = details.get("revenue", 0)
            rating = details.get("vote_average", 0)
            overview = details.get("overview", "")
            country = details.get("production_countries")[0]["iso_3166_1"] if details.get("production_countries") else "Unknown"

            cursor.execute("""
                INSERT OR IGNORE INTO movies
                (movie_id, title, genre, release_date, budget, revenue, rating, overview, country, director)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                movie_id, details.get("title"), genres, release_date,
                budget, revenue, rating, overview, country, director
            ))

            time.sleep(0.2)  # small delay per movie

        conn.commit()
        time.sleep(0.5)  # delay per page

    print(Fore.GREEN + "✅ Movies loaded successfully!")

# View movies (paginated)
def view_movies(page=1):
    per_page = 20
    offset = (page - 1) * per_page
    cursor.execute("SELECT title, genre, rating, release_date, director FROM movies LIMIT ? OFFSET ?", (per_page, offset))
    movies = cursor.fetchall()
    if not movies:
        print(Fore.YELLOW + "⚠️ No movies on this page.")
        return
    print(Fore.CYAN + f"\n--- MOVIES PAGE {page} ---")
    print("{:<30} | {:<20} | {:<6} | {:<10} | {:<20}".format("Title", "Genre", "Rating", "Release", "Director"))
    print("-" * 100)
    for m in movies:
        print(Fore.WHITE + "{:<30} | {:<20} | {:<6} | {:<10} | {:<20}".format(m[0][:30], m[1][:20], m[2], m[3], m[4][:20]))
    print("-" * 100)

# Search by title (DB + API fallback)
def search_by_title(title):
    cursor.execute("SELECT * FROM movies WHERE title LIKE ?", (f"%{title}%",))
    results = cursor.fetchall()
    if results:
        for movie in results:
            print(Fore.CYAN + f"\nTitle: {movie[1]}")
            print(Fore.YELLOW + f"Genre: {movie[2]}")
            print(f"Release Date: {movie[3]}")
            print(f"Rating: {movie[6]}")
            print(f"Director: {movie[9]}")
            print(f"Overview: {movie[7][:200]}...")
            print("-"*100)
        return
    print(Fore.YELLOW + "⚠️ Not found in DB. Fetching from TMDb...")
    movie_data = fetch_movie_details(title)
    if not movie_data:
        print(Fore.RED + "❌ Movie not found anywhere!")
        return
    print(Fore.GREEN + f"\n🎬 Movie Found: {movie_data['title']}")
    print(f"Genre: {movie_data['genre']}")
    print(f"Release Date: {movie_data['release_date']}")
    print(f"Rating: {movie_data['rating']}")
    print(f"Director: {movie_data['director']}")
    budget = movie_data.get("budget")
    revenue = movie_data.get("revenue")

    budget_str = f"${budget:,}" if budget else "N/A"
    revenue_str = f"${revenue:,}" if revenue else "N/A"

    print(f"Budget: {budget_str}")
    print(f"Revenue: {revenue_str}")
    print(f"Overview: {movie_data['overview'][:200]}...")
    add_movie_to_db(movie_data)
    print(Fore.GREEN + "✅ Saved to DB!")

# Search by director (DB + API fallback)
def search_by_director(director_name):
    cursor.execute("SELECT * FROM movies WHERE director LIKE ?", (f"%{director_name}%",))
    results = cursor.fetchall()
    if results:
        print(Fore.CYAN + f"\nMovies by {director_name} (Local DB):")
        for m in results:
            print(Fore.YELLOW + f"{m[1]} ({m[3]}) - Rating: {m[6]}")
        return
    print(Fore.YELLOW + "⚠️ Not found locally. Fetching from TMDb...")
    search_url = f"https://api.themoviedb.org/3/search/person?api_key={TMDB_API_KEY}&query={director_name}"
    data = requests.get(search_url).json()
    if not data.get("results"):
        print(Fore.RED + "❌ Director not found!")
        return
    person_id = data["results"][0]["id"]
    credits_url = f"https://api.themoviedb.org/3/person/{person_id}/movie_credits?api_key={TMDB_API_KEY}"
    credits = requests.get(credits_url).json()
    directed_movies = [m for m in credits.get("crew", []) if m.get("job") == "Director"]
    if not directed_movies:
        print(Fore.RED + "❌ No directed movies found!")
        return
    print(Fore.GREEN + f"\n🎬 Movies by {director_name} (Live API):")
    for movie in directed_movies[:5]:
        title = movie.get("title")
        print(Fore.YELLOW + f"{title}")
        details = fetch_movie_details(title)
        if details:
            add_movie_to_db(details)
        time.sleep(0.2)
    print(Fore.GREEN + "✅ Saved new movies to DB!")

# Recommendations by movie
def recommend_by_movie(movie_name):
    cursor.execute("SELECT genre FROM movies WHERE title LIKE ?", (f"%{movie_name}%",))
    result = cursor.fetchone()
    if not result:
        print(Fore.YELLOW + "⚠️ Movie not in DB. Fetching from TMDb...")
        movie_data = fetch_movie_details(movie_name)
        if not movie_data:
            print(Fore.RED + "❌ Movie not found!")
            return
        add_movie_to_db(movie_data)
        genre = movie_data["genre"]
    else:
        genre = result[0]
    cursor.execute("""
        SELECT title, genre, rating FROM movies
        WHERE genre LIKE ? AND title NOT LIKE ?
        ORDER BY rating DESC LIMIT 5
    """, (f"%{genre}%", f"%{movie_name}%"))
    recs = cursor.fetchall()
    if recs:
        print(Fore.CYAN + f"\nRecommendations based on '{movie_name}':")
        for r in recs:
            print(Fore.YELLOW + f"{r[0]} ({r[1]}) - {r[2]}")
    else:
        print(Fore.YELLOW + "⚠️ Not enough local data for recommendations.")

# Recommendations by genre
def recommend_by_genre(genre):
    cursor.execute("""
        SELECT title, genre, rating FROM movies
        WHERE genre LIKE ?
        ORDER BY rating DESC LIMIT 5
    """, (f"%{genre}%",))
    recs = cursor.fetchall()
    if recs:
        print(Fore.CYAN + f"\nTop '{genre}' movies (Local DB):")
        for r in recs:
            print(Fore.YELLOW + f"{r[0]} ({r[2]})")
        return
    print(Fore.YELLOW + "⚠️ No local data. Try another genre or add movies to DB.")

# Main menu
def main_menu():
    while True:
        print(Fore.CYAN + "\n===== TMDb Smart Movie Explorer =====")
        print(Fore.YELLOW + "1. View Movies (Paginated)")
        print(Fore.YELLOW + "2. Search Movie by Title")
        print(Fore.YELLOW + "3. Search Movies by Director")
        print(Fore.YELLOW + "4. Recommend Movies")
        print(Fore.YELLOW + "5. Exit")
        choice = input(Fore.WHITE + "Enter choice: ")
        if choice == "1":
            try:
                page = int(input("Enter page number: "))
                view_movies(page)
            except:
                print(Fore.RED + "❌ Invalid page!")
        elif choice == "2":
            name = input("Enter movie title: ")
            search_by_title(name)
        elif choice == "3":
            d = input("Enter director name: ")
            search_by_director(d)
        elif choice == "4":
            print(Fore.CYAN + "\n1. Recommend by Movie Name")
            print(Fore.CYAN + "2. Recommend by Genre")
            sub = input(Fore.WHITE + "Choice: ")
            if sub == "1":
                nm = input("Enter movie name: ")
                recommend_by_movie(nm)
            elif sub == "2":
                g = input("Enter genre: ")
                recommend_by_genre(g)
            else:
                print(Fore.RED + "❌ Invalid option!")
        elif choice == "5":
            print(Fore.GREEN + "Goodbye 👋")
            break
        else:
            print(Fore.RED + "❌ Invalid choice!")

# -------------------------------
# Run Program
# -------------------------------
if __name__ == "__main__":
    # Run this only once to fetch popular movies
    # auto_fetch_movies(total_pages=10)

    main_menu()
    conn.close()