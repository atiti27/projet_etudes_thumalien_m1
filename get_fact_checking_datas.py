import os
import re
import requests
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, Column, Integer, Text, String, DateTime, ForeignKey, select, insert
from db import engine 
load_dotenv()

# Initialiser le metadata
metadata = MetaData()

# Définition de la table posts
posts_table = Table(
    'posts', metadata,
    autoload_with=engine
)

# Définir la table fact_checks si elle n'existe pas
fact_checks_table = Table(
    'fact_checks', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('post_id', Integer, ForeignKey('posts.id')),
    Column('claim_text', Text),
    Column('source_title', String(255)),
    Column('source_link', String(255)),
    Column('source_excerpt', Text),
    Column('source_site', String(255)),
)

# Crée la table dans la base si elle n'existe pas
metadata.create_all(engine)

# Extraire des mots-clés d’un texte
def extract_keywords(text):
    stop_words = {
        "le", "la", "les", "de", "des", "du", "un", "une", "et", "à", "dans", "sur",
        "pour", "par", "avec", "au", "aux", "ce", "ces", "se", "sa", "son"
    }
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords

# Construire une requête avec ou sans "OR"
def build_query(keywords, use_or=False):
    op = " OR " if use_or else " "
    return op.join(keywords)

# Interroger l’API Google Fact Check Tools
def search_fact_source_flexible(title):
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
                return claims[0]
        else:
            print(f"Erreur API pour la requête '{q}' : {response.status_code}")
    return None

# Programme principal
def main():
    with engine.connect() as conn:
        result = conn.execute(select(posts_table.c.id, posts_table.c.title))
        posts = result.fetchall()

        for post in posts:
            post_id = post.id
            title = post.title

            # Vérifie si une vérification existe déjà
            existing = conn.execute(
                select(fact_checks_table.c.id).where(fact_checks_table.c.post_id == post_id)
            ).fetchone()
            if existing:
                continue

            claim = search_fact_source_flexible(title)
            if claim:
                review = claim.get("claimReview", [{}])[0]
                conn.execute(
                    insert(fact_checks_table).values(
                        post_id=post_id,
                        claim_text=claim.get("text"),
                        source_title=review.get("title"),
                        source_link=review.get("url"),
                        source_excerpt=review.get("textualRating"),
                        source_site=review.get("publisher", {}).get("name")
                    )
                )
                print(f"✅ Fact-check enregistré pour le post #{post_id}")
            else:
                print(f"❌ Aucun fact-check trouvé pour : '{title}'")

if __name__ == "__main__":
    main()
