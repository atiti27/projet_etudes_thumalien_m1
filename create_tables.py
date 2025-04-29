from sqlalchemy import Table, Column, Integer, Text, TIMESTAMP, MetaData, ForeignKey
from db import get_engine

engine = get_engine()
metadata = MetaData()

posts = Table("posts", metadata,
    Column("id", Integer, primary_key=True),
    Column("title", Text),
    Column("content", Text),
    Column("author", Text),
    Column("publi_date", TIMESTAMP),
    Column("link", Text, unique=True),
    Column("nbr_like", Integer),
    Column("nbr_comment", Integer),
    Column("nbr_repost", Integer),
    Column("hashtags", Text),
)

comments = Table("comments", metadata,
    Column("id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("posts.id", ondelete="CASCADE")),
    Column("content", Text),
    Column("author", Text),
    Column("publi_date", TIMESTAMP),
    Column("link", Text, unique=True),
    Column("nbr_like", Integer),
    Column("nbr_comment", Integer),
    Column("nbr_repost", Integer),
)

metadata.create_all(engine)
print("Tables créées avec succès.")
