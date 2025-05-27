import os
import re
import requests
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, Column, Integer, Text, String, ForeignKey, select, insert
from db import engine

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

def extract_keywords(text):
    stop_words = {
        "le", "la", "les", "de", "des", "du", "un", "une", "et", "à", "dans", "sur",
        "pour", "par", "avec", "au", "aux", "ce", "ces", "se", "sa", "son"
    }
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords

def build_query(keywords, use_or=False):
    op = " OR " if use_or else " "
    return op.join(keywords)

def search_fact_sources(title, max_claims=3, max_reviews=3):
    keywords = extract_keywords(title)
    queries = [title] if not keywords else [build_query(keywords), build_query(keywords, use_or=True)]

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
                # Limit claims and limit reviews for each claim
                limited_claims = []
                for claim in claims[:max_claims]:
                    claim_reviews = claim.get("claimReview", [])[:max_reviews]
                    claim["claimReview"] = claim_reviews
                    limited_claims.append(claim)
                return limited_claims
        else:
            print(f"Erreur API pour la requête '{q}' : {response.status_code}")
    return []

def main():
    with engine.connect() as conn:
        result = conn.execute(select(posts_table.c.id, posts_table.c.title))
        posts = result.fetchall()

        for post in posts:
            post_id = post.id
            title = post.title

            # Vérifie si déjà des fact-checks pour ce post pour éviter doublons
            existing = conn.execute(
                select(fact_checks_table.c.id).where(fact_checks_table.c.post_id == post_id)
            ).fetchone()
            if existing:
                continue

            claims = search_fact_sources(title)
            if claims:
                for claim in claims:
                    claim_id = claim.get("claimReview", [{}])[0].get("claimReviewed", "") or claim.get("text", "")
                    for review in claim.get("claimReview", []):
                        fact_check = {
                            "post_id": post_id,
                            "claim_id": claim_id,
                            "claim_text": claim.get("text", ""),
                            "source_title": review.get("title", ""),
                            "source_link": review.get("url", ""),
                            "source_excerpt": review.get("textualRating", ""),
                            "source_site": review.get("publisher", {}).get("name", "")
                        }
                        # Insertion dans la table fact_checks
                        conn.execute(fact_checks_table.insert(), fact_check)
                conn.commit()
                print(f"✅ {len(claims)} claim(s) et jusqu'à 3 reviews chacun enregistrés pour le post #{post_id}")
            else:
                print(f"❌ Aucun fact-check trouvé pour : '{title}'")

if __name__ == "__main__":
    main()

