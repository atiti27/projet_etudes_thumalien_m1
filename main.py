import os
from atproto_client import Client
import dotenv
import pandas as pd

from extract_data import extract_comment_from_post, extract_data_from_post

dotenv.load_dotenv()

user_name = os.getenv("USER")
password = os.getenv("PASSWORD")
did = os.getenv("DID")

client = Client()
client.login(user_name, password)

record_key_france = "aaafczzvnktbe"

# Construire l'URI du flux public
public_feed_uri = f'at://{did}/app.bsky.feed.generator/{record_key_france}'
print(f"Public feed URI for French press: {public_feed_uri}")

try:
    # Collecter les publications du flux public
    response = client.app.bsky.feed.get_feed({
        "feed": public_feed_uri,
        "limit": 10
    })

    feed = response.feed
    print(f"Number of posts retrieved: {len(feed)}")
except Exception as e:
    print(f"Error retrieving posts: {e}")
    feed = []

df_posts = pd.DataFrame(columns=["id", "title", "content", "author", "publi_date", "link", "nbr_like", "nbr_comment", "nbr_repost", "hashtags"])
# Mettre la logique de récupération de l'id du post depuis la BDD (à faire plus tard)
post_id = 0
for post in feed:
    obj_post = extract_data_from_post(post, client)
    if obj_post is None:
        continue
    df_comments = pd.DataFrame(columns=["id", "post_id", "content", "author", "publi_date", "link"])
    list_comments = obj_post["comments"]
    for comment in list_comments:
        obj_comment = extract_comment_from_post(comment)
        obj_comment["post_id"] = post_id
        # L'id du commentaire sera lui automatiquement incrémenté dans la BDD (contrairement à celui du post)
        df_comments = pd.concat([df_comments, pd.DataFrame([obj_comment])], ignore_index=True)
    obj_post["id"] = post_id
    post_id += 1
    df_posts = pd.concat([df_posts, pd.DataFrame([obj_post])], ignore_index=True)

    # Dans cette boucle, insérer les données des commentaires dans la base de données (faire fonction)

# À la fin de la boucle for, insérer les données des posts dans la base de données (faire fonction)


