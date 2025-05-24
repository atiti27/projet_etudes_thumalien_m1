import os
import re
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def extract_keywords(text):
    stop_words = {
        "le", "la", "les", "de", "des", "du", "un", "une", "et", "à", "dans", "sur", 
        "pour", "par", "avec", "au", "aux", "ce", "ces", "se", "sa", "son"
    }
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords

def build_query(keywords, use_or=False):
    op = " OR " if use_or else " AND "
    return op.join(keywords)

def search_fact_source_flexible(title):
    keywords = extract_keywords(title)
    if not keywords:
        queries = [title]
    else:
        queries = [build_query(keywords, use_or=False), build_query(keywords, use_or=True)]

    for q in queries:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': q,
            'apiKey': os.getenv("NEWSAPI_KEY"),
            'language': 'fr',
            'pageSize': 1,
            'sortBy': 'relevancy'
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            articles = response.json().get('articles', [])
            if articles:
                return articles[0]
        else:
            print(f"API error for query '{q}': {response.status_code}")
    return None

def main():
    simulated_posts = [
        {"id": 1, "title": "Les élections présidentielles approchent en France"},
        {"id": 2, "title": "La crise énergétique impacte les marchés européens"},
        {"id": 3, "title": "Nouvelles avancées dans la lutte contre le cancer"},
        {"id": 4, "title": "Les innovations technologiques en 2025"},
        {"id": 5, "title": "Le changement climatique et ses effets sur la biodiversité"},
        {"id": 6, "title": "L'impact économique du télétravail"},
        {"id": 7, "title": "La réforme des retraites suscite des débats"},
        {"id": 8, "title": "La croissance du marché des véhicules électriques"},
        {"id": 9, "title": "Les derniers résultats du tournoi de tennis"},
        {"id": 10, "title": "Le rôle des réseaux sociaux dans la politique"},
        {"id": 11, "title": "Les tendances mode printemps-été 2025"},
        {"id": 12, "title": "L'importance de la cybersécurité dans les entreprises"},
        {"id": 13, "title": "Les avancées en intelligence artificielle"},
        {"id": 14, "title": "La protection des données personnelles"},
        {"id": 15, "title": "Les défis du secteur agricole face au climat"},
        {"id": 16, "title": "Les manifestations pour la justice sociale"},
        {"id": 17, "title": "Les innovations dans l'industrie spatiale"},
        {"id": 18, "title": "Le développement des énergies renouvelables"},
        {"id": 19, "title": "La réforme de l'éducation nationale"},
        {"id": 20, "title": "Les avancées médicales contre les maladies neurodégénératives"}
    ]

    fact_check_data = []

    for post in simulated_posts:
        article = search_fact_source_flexible(post["title"])

        if article is None:
            print(f"Aucun article trouvé pour : '{post['title']}'")
            fact_check_data.append({
                "post_id": post["id"],
                "title": post["title"],
                "result": None,
                "message": "Aucun article trouvé pour ce titre."
            })
        else:
            fact_check_data.append({
                "post_id": post["id"],
                "title": post["title"],
                "result": {
                    "source_title": article.get("title"),
                    "source_link": article.get("url"),
                    "source_excerpt": article.get("description"),
                    "source_date": datetime.strptime(article.get("publishedAt"), "%Y-%m-%dT%H:%M:%SZ").isoformat() if article.get("publishedAt") else None,
                    "source_author": article.get("author"),
                    "source_site": article.get("source", {}).get("name")
                }
            })

    with open("fact_check_results.json", "w", encoding="utf-8") as f:
        json.dump(fact_check_data, f, ensure_ascii=False, indent=4)

    print("Résultats sauvegardés dans fact_check_results.json")

if __name__ == "__main__":
    main()
