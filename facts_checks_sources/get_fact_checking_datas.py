import os
import re
import requests
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, select
from db.db_connection import engine

import difflib

load_dotenv()

metadata = MetaData()

posts_table = Table(
    'posts', metadata,
    autoload_with=engine
)

fact_checks_table = Table(
    "fact_checks_sources", metadata,
    autoload_with=engine
)

metadata.create_all(engine)

def extract_keywords(text, min_length=3):
    """Extrait les mots-clés d'un texte en filtrant les mots vides"""
    stop_words = {
        "le", "la", "les", "de", "des", "du", "un", "une", "et", "à", "dans", "sur",
        "pour", "par", "avec", "au", "aux", "ce", "ces", "se", "sa", "son"
    }
    # Nettoyer le texte
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = re.findall(r'\b\w+\b', text)
    
    # Filtrer les mots vides et les mots trop courts
    keywords = [w for w in words if w not in stop_words and len(w) >= min_length]
    
    # Retourner les mots-clés uniques en gardant l'ordre
    seen = set()
    unique_keywords = []
    for word in keywords:
        if word not in seen:
            seen.add(word)
            unique_keywords.append(word)
    
    return unique_keywords[:10]  # Limiter à 10 mots-clés pour éviter les requêtes trop longues

def build_search_queries(keywords):
    """Construit différentes requêtes de recherche à partir des mots-clés"""
    if not keywords:
        return []
    
    queries = []
    
    # Requête avec tous les mots-clés (AND)
    if len(keywords) > 1:
        queries.append(" ".join(keywords[:3]))  # Limiter à 3 mots pour AND
    
    # Requête avec OR pour les mots-clés les plus importants
    queries.append(" OR ".join(keywords[:3]))
    
    # Requêtes individuelles pour les mots-clés les plus importants
    for keyword in keywords[:2]:
        queries.append(keyword)
    
    return queries

def calculate_similarity(text1, text2):
    """Calcule la similarité entre deux textes"""
    if not text1 or not text2:
        return 0.0
    
    # Normaliser les textes
    text1_norm = re.sub(r'[^\w\s]', '', text1.lower()).strip()
    text2_norm = re.sub(r'[^\w\s]', '', text2.lower()).strip()
    
    # Calculer la similarité avec difflib
    similarity = difflib.SequenceMatcher(None, text1_norm, text2_norm).ratio()
    
    # Calculer aussi la similarité des mots-clés
    keywords1 = set(extract_keywords(text1))
    keywords2 = set(extract_keywords(text2))
    
    if keywords1 and keywords2:
        keyword_similarity = len(keywords1.intersection(keywords2)) / len(keywords1.union(keywords2))
        # Moyenne pondérée
        similarity = 0.7 * similarity + 0.3 * keyword_similarity
    
    return round(similarity, 3)

def search_fact_check_api(query, api_key, max_results = 10):
    """Recherche dans l'API Google Fact Check Tools"""
    if not api_key:
        print("⚠️  Clé API Fact Check manquante")
        return []
    
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {
        'query': query,
        'languageCode': 'fr',
        'key': api_key,
        'pageSize': max_results
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("claims", [])
        else:
            print(f"⚠️  Erreur API ({response.status_code}) pour la requête: {query}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Erreur de connexion API: {e}")
        return []
    
def process_fact_check_claims(claims, original_text):
    """Traite les résultats de l'API fact-checking"""
    results = []
    
    for claim in claims:
        claim_text = claim.get("text", "")
        claim_reviews = claim.get("claimReview", [])
        
        if not claim_reviews:
            continue
        
        # Calculer la similarité avec le texte original
        similarity = calculate_similarity(original_text, claim_text)
        
        # Ne garder que les résultats avec une similarité minimale
        if similarity < 0.3:
            continue
        
        claim_id = claim.get("claimReview", [{}])[0].get("claimReviewed", "") or claim.get("text", "")
        for review in claim_reviews:
            
            result = {
                "claim_id": claim_id,
                "claim_text": claim_text,
                "source_title": review.get("title", ""),
                "source_link": review.get("url", ""),
                "source_excerpt": review.get("textualRating", ""),
                "source_site": review.get("publisher", {}).get("name", ""),
                "similarity_score": similarity
            }
            
            results.append(result)
    
    # Trier par score de similarité décroissant
    results.sort(key=lambda x: x.similarity_score, reverse=True)
    return results[:3]  # Retourner les 3 meilleurs résultats

def get_fact_checking_data():
    with engine.connect() as conn:
        result = conn.execute(select(posts_table.c.id, posts_table.c.title))
        posts = result.fetchall()

        api_key = os.getenv("FACTCHECK_API_KEY")

        for post in posts:
            post_id = post.id
            title = post.title

            # Vérifie si déjà des fact-checks pour ce post pour éviter doublons
            existing = conn.execute(
                select(fact_checks_table.c.id).where(fact_checks_table.c.post_id == post_id)
            ).fetchone()
            if existing:
                continue

            search_queries = build_search_queries(title)
            for query in search_queries:
                claims = search_fact_check_api(query, api_key)

                if claims:
                    results = process_fact_check_claims(claims, title)
                    # Insertion des résultats dans la base de données
                    for result in results:
                        fact_check = {
                            "post_id": post_id,
                            "claim_id": result.get("claim_id", ""),
                            "claim_text": result.get("claim_text", ""),
                            "source_title": result.get("source_title", ""),
                            "source_link": result.get("source_link", ""),
                            "source_excerpt": result.get("source_excerpt", ""),
                            "source_site": result.get("source_site", "")
                        }
                        conn.execute(fact_checks_table.insert(), fact_check)
                    conn.commit()
                    print(f"✅ {len(results)} fact-check(s) trouvé(s) pour le post #{post_id} : '{title}'")
                else:
                    print(f"❌ Aucun fact-check trouvé pour : '{title}'")

if __name__ == "__main__":
    get_fact_checking_data()

