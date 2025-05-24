import os
import re
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Extract keywords by filtering out common French stopwords
def extract_keywords(text):
    stop_words = {
        "le", "la", "les", "de", "des", "du", "un", "une", "et", "à", "dans", "sur", 
        "pour", "par", "avec", "au", "aux", "ce", "ces", "se", "sa", "son"
    }
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords

# Builds query from keyword list
def build_query(keywords, use_or=False):
    op = " " if not use_or else " OR "
    return op.join(keywords)

# Searches Google Fact Check Tools API for existing claims
def search_fact_source_flexible(title):
    keywords = extract_keywords(title)
    queries = [title] if not keywords else [build_query(keywords, use_or=False), build_query(keywords, use_or=True)]

    for q in queries:
        url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        params = {
            'query': q,
            'languageCode': 'fr',
            'key': os.getenv("FACTCHECK_API_KEY")
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            claims = response.json().get("claims", [])
            if claims:
                return claims[0]  # Return the first matching claim
        else:
            print(f"Erreur API pour la requête '{q}' : {response.status_code}")
    return None

# Main function: simulate posts and verify them using fact-check API
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
        {"id": 10, "title": "Le rôle des réseaux sociaux dans la politique"}
    ]

    fact_check_data = []

    for post in simulated_posts:
        claim = search_fact_source_flexible(post["title"])

        if claim is None:
            print(f"Aucune vérification trouvée pour : '{post['title']}'")
            fact_check_data.append({
                "post_id": post["id"],
                "title": post["title"],
                "result": None,
                "message": "Aucune vérification trouvée pour ce titre."
            })
        else:
            review = claim.get("claimReview", [{}])[0]
            fact_check_data.append({
                "post_id": post["id"],
                "title": post["title"],
                "result": {
                    "claim_text": claim.get("text"),
                    "source_title": review.get("title"),
                    "source_link": review.get("url"),
                    "source_excerpt": review.get("textualRating"),
                    "source_site": review.get("publisher", {}).get("name")
                }
            })

    with open("fact_check_results.json", "w", encoding="utf-8") as f:
        json.dump(fact_check_data, f, ensure_ascii=False, indent=4)

    print("Résultats sauvegardés dans fact_check_results.json")

if __name__ == "__main__":
    main()
