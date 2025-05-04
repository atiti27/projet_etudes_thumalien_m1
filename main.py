import os
from atproto_client import Client
import dotenv
import pandas as pd
from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, Text, insert

from extract_data import extract_comment_from_post, extract_data_from_post
from db import get_engine

dotenv.load_dotenv()

user_name = os.getenv("USER")
password = os.getenv("PASSWORD")
did = os.getenv("DID")

client = Client()
client.login(user_name, password)

record_key_france = "aaafczzvnktbe"

public_feed_uri = f'at://{did}/app.bsky.feed.generator/{record_key_france}'
print(f"Public feed URI for French press: {public_feed_uri}")

try:
    response = client.app.bsky.feed.get_feed({
        "feed": public_feed_uri,
        "limit": 10
    })
    feed = response.feed
    print(f"Number of posts retrieved: {len(feed)}")
except Exception as e:
    print(f"Error retrieving posts: {e}")
    feed = []

engine = get_engine()

# Définir les tables avec SQLAlchemy
metadata = MetaData()

posts_table = Table(
    'posts', metadata,
    Column('id', Integer, primary_key=True),
    Column('title', Text),
    Column('content', Text),
    Column('author', String(255)),
    Column('publi_date', DateTime),
    Column('link', String(255)),
    Column('nbr_like', Integer),
    Column('nbr_comment', Integer),
    Column('nbr_repost', Integer),
    Column('hashtags', Text),
)

comments_table = Table(
    'comments', metadata,
    Column('id', Integer, primary_key=True),
    Column('post_id', Integer),
    Column('content', Text),
    Column('author', String(255)),
    Column('publi_date', DateTime),
    Column('link', String(255)),
    Column('nbr_like', Integer),
    Column('nbr_comment', Integer),
    Column('nbr_repost', Integer),
)

metadata.create_all(engine)

post_id = 1

for post in feed:
    obj_post = extract_data_from_post(post, client)
    if obj_post is None:
        continue

    obj_post["id"] = post_id
    try:
        with engine.begin() as conn:
            conn.execute(insert(posts_table), obj_post)
        print(f"Inserted post with ID {post_id}")
    except Exception as e:
        print(f"Error inserting post {post_id}: {e}")
        continue

    list_comments = obj_post.pop("comments", [])
    for comment in list_comments:
        obj_comment = extract_comment_from_post(comment)
        obj_comment["post_id"] = post_id
        try:
            with engine.begin() as conn:
                conn.execute(insert(comments_table), obj_comment)
            print(f"Inserted comment for post ID {post_id}")
        except Exception as e:
            print(f"Error inserting comment for post {post_id}: {e}")

    post_id += 1
