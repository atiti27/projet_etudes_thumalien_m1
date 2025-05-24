from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import re
import emoji
import spacy

# Fonction utile pour notre cas où dans une première version, nous ne traitons que les tweets en français
def filter_by_language(text, confidence_threshold=0.8):
    """
    Filtre le texte pour ne garder que la langue française.
    """
    model_name = "papluca/xlm-roberta-base-language-detection"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

    nlp = pipeline("text-classification", model=model, tokenizer=tokenizer)

    result = nlp(text)
    language = result[0]['label']
    confidence = result[0]['score']

    return language == 'fr' and confidence >= confidence_threshold

def filter_short_text(text):
    """
    Filtre les textes courts en fonction de la longueur minimale spécifiée.
    """
    min_length = 3
    return len(text) >= min_length

def normalize_data(brut_text):
    """
    Normalise le texte en remplaçant les emojis par du texte, en transformant les ligatures pour une meilleure compréhension par les modèles de langage,
    et en supprimant les caractères spéciaux.
    """

    print(f"Original text: {brut_text}")
    # Conversion des emojis en texte
    text_with_converted_emoji = emoji.demojize(brut_text, language="fr")

    # Suppression des mentions, des liens et des hashtags
    text_without_mentions_and_links = re.sub(r'#\w+|@\w+|https?://\S+', '', text_with_converted_emoji)

    # Suppression des caractères spéciaux
    words = [
        word for word in text_without_mentions_and_links.split()
        if re.match(r"^[a-zA-ZÀ-ÖØ-öø-ÿ'’]+$", word)
        or "'" in word or "’" in word
        or re.match(r':\w+:', word) or re.match(r'^\w+.$', word)
    ]

    clean_text = " ".join(words)

    print(f"Cleaned text normalize_data: {clean_text}")

    return clean_text

def lemmatization_text(text):
    nlp = spacy.load('fr_core_news_sm')
    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if not token.is_stop]
    clean_text = " ".join(tokens)
    print(f"Cleaned text lemmatization_text: {clean_text}")
    return clean_text

if __name__ == "__main__":
    text = "Hello ❤️. https://www.example.com @user #coucou c'est tout pour moi je suis élégante."
    normalized_text = normalize_data(text)
    lemmatized_text = lemmatization_text(normalized_text)
    print(f"Texte normalisé : {lemmatized_text}")