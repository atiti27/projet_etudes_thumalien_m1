from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from sqlalchemy import text
from db.db_connection import get_engine
from deep_translator import GoogleTranslator
from db.create_tables import emotional_analysis_roberta

model_name = "j-hartmann/emotion-english-distilroberta-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
emotion_pipeline_roberta = pipeline("text-classification", model=model, tokenizer=tokenizer, top_k=None)

engine = get_engine()
translator_roberta = GoogleTranslator(source='fr', target='en')

def analyze_posts():
    with engine.connect() as connection:
        # Récupérer les posts qui n'ont pas encore été analysés
        posts_table = connection.execute(text("""
            SELECT p.id, p.content 
            FROM posts p
            LEFT JOIN emotional_analysis_roberta eab 
            ON p.id = eab.post_id
            WHERE eab.post_id IS NULL
            ORDER BY p.id
        """)).fetchall()

        for post in posts_table:
            post_id, content = post
            try:
                emotional_data = analyze_emotions(content, post_id)
            except Exception as e:
                print(f"Erreur lors de l analyse des emotions pour le post ID {post_id}: {e}")
                continue
            connection.execute(emotional_analysis_roberta.insert(), emotional_data)
            connection.commit()

def analyze_emotions(content, post_id):
    translated_content = translator_roberta.translate(content)
    emotions = emotion_pipeline_roberta(translated_content)
    emotion_scores = {emotion['label']: int(emotion['score'] * 100) for emotion in emotions[0]}
    emotional_data = {
        "post_id": post_id,
        "disgust": emotion_scores.get("disgust", 0),
        "sadness": emotion_scores.get("sadness", 0),
        "fear": emotion_scores.get("fear", 0),
        "anger": emotion_scores.get("anger", 0),
        "neutral": emotion_scores.get("neutral", 0),
        "surprise": emotion_scores.get("surprise", 0),
        "joy": emotion_scores.get("joy", 0),
    }
    print(f"Analyse emotionnelle pour le post ID {post_id}")
    return emotional_data

if __name__ == "__main__":
    analyze_posts()