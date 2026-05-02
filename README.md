# 🎬 Movie Recommendation System

## 📌 Overview

This project is a Movie Recommendation System that suggests similar movies based on user input. It uses content-based filtering techniques to find relationships between movies.

## 🛠️ Technologies Used

* Python
* Pandas
* NumPy
* Scikit-learn
* NLP (CountVectorizer / TF-IDF)

## ⚙️ How It Works

* Data preprocessing and cleaning
* Feature extraction from:

  * Genres
  * Keywords
  * Cast
  * Crew
* Text vectorization using NLP techniques
* Similarity calculation using Cosine Similarity
* Recommends top similar movies

## 🔍 Features

* Input a movie name
* Get top 5–10 similar movie recommendations
* Fast and efficient similarity search

## 📂 Project Structure

* `movie\_recommender.py` → Main logic
* `movies.csv` → Dataset
* `similarity.pkl` → Precomputed similarity matrix (if used)

## 🚀 Example

Input: Batman  
Output:

* The Dark Knight
* Batman Begins
* The Dark Knight Rises

## Output Preview

![Project Output](https://github.com/Rony94022/movie-recommendation-system/blob/main/Screenshot_Output.png?raw=true)

## 📈 Outcome

Built a basic recommendation engine and understood real-world applications of machine learning in entertainment platforms.

## 🔮 Future Improvements

* Add collaborative filtering
* Deploy as a web app (Streamlit)
* Improve UI/UX

