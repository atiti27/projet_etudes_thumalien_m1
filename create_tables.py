from sqlalchemy import Table, Column, Integer, Text, Float, TIMESTAMP, Boolean, MetaData, ForeignKey, String, DateTime
from db import get_engine

engine = get_engine()
metadata = MetaData()

posts_table = Table(
    'posts', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('title', Text),
    Column('content', Text),
    Column('author', String(255)),
    Column('publi_date', DateTime),
    Column('link', String(255), unique=True), 
    Column('nbr_like', Integer),
    Column('nbr_comment', Integer),
    Column('nbr_repost', Integer),
    Column('hashtags', Text),
)

comments_table = Table(
    'comments', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('post_id', Integer),
    Column('content', Text),
    Column('author', String(255)),
    Column('publi_date', DateTime),
    Column('link', String(255), unique=True),
    Column('nbr_like', Integer),
    Column('nbr_comment', Integer),
    Column('nbr_repost', Integer),
)

emotional_analysis_bert = Table("emotional_analysis_bert", metadata,
    Column("id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("posts.id", ondelete="CASCADE")),
    Column("anger", Integer, default=0),
    Column("joy", Integer, default=0),
    Column("love", Integer, default=0),
    Column("sadness", Integer, default=0),
    Column("fear", Integer, default=0),
    Column("surprise", Integer, default=0),
)

emotional_analysis_roberta = Table("emotional_analysis_roberta", metadata,
    Column("id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("posts.id", ondelete="CASCADE")),
    Column("disgust", Integer, default=0),
    Column("sadness", Integer, default=0),
    Column("fear", Integer, default=0),
    Column("anger", Integer, default=0),
    Column("neutral", Integer, default=0),
    Column("surprise", Integer, default=0),
    Column("joy", Integer, default=0),
)

fact_checks_table = Table(
    "fact_checks_sources", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("post_id", Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
    Column("claim_id", String(255), nullable=False),
    Column("claim_text", Text, nullable=False),
    Column("source_title", String(255)),
    Column("source_link", String(255)),
    Column("source_excerpt", Text),
    Column("source_site", String(255)),
)

comprehensive_analysis_table = Table(
    "comprehensive_reliability_analysis", metadata,
    Column("id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("posts.id", ondelete="CASCADE")),
    
    # Classification RoBERTa
    Column("content_category", String(50)),
    Column("content_confidence", Float, default=0.0),
    
    # Détection fake news RoBERTa
    Column("is_fake_news", Integer, default=0),
    Column("fake_news_confidence", Float, default=0.0),
    
    # Score de fiabilité basé sur le contenu
    Column("content_reliability_score", Float, default=0.0),
    
    # Fact-checking externe
    Column("has_fact_check", Boolean, default=False),
    Column("fact_check_rating", String(100)),
    Column("fact_check_source", String(255)),
    Column("external_reliability_score", Float, default=0.0),
    
    # Score global synthétique
    Column("global_reliability_score", Float, default=0.0),
    Column("final_category", String(50)),
    Column("confidence_level", String(20)), 
)

if __name__ == "__main__":
    metadata.create_all(engine)
    print("Tables créées avec succès.")
