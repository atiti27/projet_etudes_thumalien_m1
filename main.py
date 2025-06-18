import os
from atproto_client import Client
import dotenv
from sqlalchemy import insert, select
from extract_data import extract_comment_from_post, extract_data_from_post
from db.db_connection import get_engine
from db.create_tables import metadata, posts_table, comments_table
from model_analysis.emotional.roberta import analyze_posts as analyze_emotions_roberta
from model_analysis.fake_news_detection.fake_news_detection_roberta import (
    analyze_posts_comprehensive,
    generate_synthetic_report,
    fix_existing_inconsistencies
)
from facts_checks_sources.get_fact_checking_datas import get_fact_checking_data

# Charger les variables d'environnement
dotenv.load_dotenv()

user_name = os.getenv("USER")
password = os.getenv("PASSWORD")
did = os.getenv("DID")

# Connexion au client Bluesky
client = Client()
client.login(user_name, password)

record_key_france = "aaafczzvnktbe"
public_feed_uri = f'at://{did}/app.bsky.feed.generator/{record_key_france}'
print(f"Public feed URI for French press: {public_feed_uri}")

# Récupération des posts
try:
    response = client.app.bsky.feed.get_feed({
        "feed": public_feed_uri,
        "limit": 2
    })
    feed = response.feed
    print(f"Number of posts retrieved: {len(feed)}")
except Exception as e:
    print(f"Error retrieving posts: {e}")
    feed = []

# Connexion à la base de données
engine = get_engine()
metadata.create_all(engine)  # Crée les tables si elles n'existent pas

# Insertion des données
for post in feed:
    obj_post = extract_data_from_post(post, client)
    if obj_post is None:
        continue

    link = obj_post.get("link")
    if not link:
        print("Lien du post manquant, on saute ce post.")
        continue

    # Vérifier si le post existe déjà
    with engine.begin() as conn:
        result = conn.execute(select(posts_table.c.id).where(posts_table.c.link == link))
        existing_post_id = result.scalar()

    if existing_post_id:
        print(f"Post déjà présent avec link: {link} (ID {existing_post_id})")
        continue

    list_comments = obj_post.pop("comments", [])

    # Insertion du post
    try:
        with engine.begin() as conn:
            result = conn.execute(
                insert(posts_table).returning(posts_table.c.id),
                obj_post
            )
            post_db_id = result.scalar()
        print(f"Post inséré avec ID {post_db_id}")
    except Exception as e:
        print(f"Erreur lors de l'insertion du post: {e}")
        continue

    # Insertion des commentaires associés
    for comment in list_comments:
        obj_comment = extract_comment_from_post(comment)
        if obj_comment is None:
            continue

        obj_comment["post_id"] = post_db_id
        comment_link = obj_comment.get("link")

        if not comment_link:
            print("Commentaire sans lien, insertion ignorée.")
            continue

        # Vérifier si le commentaire existe déjà
        with engine.begin() as conn:
            result = conn.execute(select(comments_table.c.id).where(comments_table.c.link == comment_link))
            existing_comment_id = result.scalar()

        if existing_comment_id:
            print(f"Commentaire déjà présent avec link: {comment_link} (ID {existing_comment_id})")
            continue

        # Insertion du commentaire
        try:
            with engine.begin() as conn:
                conn.execute(insert(comments_table), obj_comment)
            print(f"Commentaire inséré pour le post ID {post_db_id}")
        except Exception as e:
            print(f"Erreur lors de l'insertion du commentaire: {e}")

# Lancement des analyses émotionnelles
try:
    print("Démarrage de l'analyse émotionnelle...")
    analyze_emotions_roberta()
    print("Analyse émotionnelle terminée.")
except Exception as e:
    print(f"Erreur lors de l'analyse émotionnelle: {e}")

# Lancement de l'analyse de détection de désinformation
try:
    print("🔍 ANALYSE COMPLÈTE DE FIABILITÉ AVEC ROBERTA")
    print("Fonctionnalités: Classification, Détection fake news, Utilisation des fact-checks existants")
    
    # Message d'information sur la complémentarité
    print("\n💡 Exécution du script get_fact_checking_datas")
    get_fact_checking_data()
    
    # Corriger les incohérences existantes
    fix_existing_inconsistencies()
    
    # Lancer l'analyse complète
    analyze_posts_comprehensive()
    
    # Générer le rapport
    generate_synthetic_report()
    print("Analyse de détection de désinformation terminée.")
except Exception as e:
    print(f"Erreur lors de l'analyse de détection de désinformation: {e}")
