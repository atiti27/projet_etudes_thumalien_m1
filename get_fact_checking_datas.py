import os
import re
import requests
from datetime import datetime
from sqlalchemy import create_engine, MetaData, select, insert
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
    # Connexion à la base
    engine = create_engine(os.getenv("DATABASE_URL"))
    metadata = MetaData()
    metadata.reflect(bind=engine)

    posts_table = metadata.tables['posts']
    fact_check_sources = metadata.tables['fact_check_sources']

    with engine.connect() as connection:
        # Récupérer 20 posts (id, title)
        result = connection.execute(select(posts_table.c.id, posts_table.c.title).limit(20))

        for row in result:
            post_id = row.id
            title = row.title

            article = search_fact_source_flexible(title)

            if article is None:
                print(f"Aucun article trouvé pour : '{title}'")
                # Optionnel: insérer une ligne vide ou un log dans la base
            else:
                # Préparer l'insertion dans fact_check_sources
                insert_stmt = insert(fact_check_sources).values(
                    post_id=post_id,
                    source_title=article.get("title"),
                    source_link=article.get("url"),
                    source_excerpt=article.get("description"),
                    source_date=datetime.strptime(article.get("publishedAt"), "%Y-%m-%dT%H:%M:%SZ") if article.get("publishedAt") else None,
                    source_author=article.get("author"),
                    source_site=article.get("source", {}).get("name")
                )
                connection.execute(insert_stmt)
                print(f"Article inséré pour post ID {post_id}")

if __name__ == "__main__":
    main()
