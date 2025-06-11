from model_analysis.emotional.bert import emotion_pipeline_bert, translator_bert
from model_analysis.emotional.roberta import emotion_pipeline_roberta, translator_roberta
from sklearn.metrics import classification_report, confusion_matrix
import time
import matplotlib.pyplot as plt
import seaborn as sns

test_data = [
    {"text": "C'est inadmissible, je suis furieux !", "label": "anger"},
    {"text": "Tu m'as vraiment mis en colère avec ton attitude.", "label": "anger"},
    {"text": "Je n'ai jamais été aussi heureux de toute ma vie.", "label": "joy"},
    {"text": "Quel bonheur de te revoir après tout ce temps !", "label": "joy"},
    {"text": "Je crains que tout cela finisse mal.", "label": "fear"},
    {"text": "Cette situation me fait vraiment peur.", "label": "fear"},
    {"text": "Je me sens tellement seul ce soir.", "label": "sadness"},
    {"text": "C'est difficile de cacher ma tristesse.", "label": "sadness"},
    {"text": "Bien sûr, parce que tout va toujours parfaitement bien dans ma vie.", "label": "sarcasm"},
    {"text": "Oh, génial, encore une panne d'électricité, quelle chance !", "label": "sarcasm"},
    {"text": "Je suis tellement en colère contre toi !", "label": "anger"},
    {"text": "C'est la meilleure journée de ma vie !", "label": "joy"},
    {"text": "J'ai tellement peur de ce qui va arriver.", "label": "fear"},
    {"text": "Oh super, encore une journée parfaite... vraiment génial.", "label": "sarcasm"},
    {"text": "Je suis triste et déçu par cette situation.", "label": "sadness"},
    {"text": "C'est tellement effrayant, je ne sais pas quoi faire.", "label": "fear"},
    {"text": "Je suis tellement heureux aujourd'hui !", "label": "joy"},
    {"text": "Oh, merci, c'est tellement utile... ou pas.", "label": "sarcasm"},
]

def get_predictions(pipeline, translator, data):
    predictions = []
    for item in data:
        translated_text = translator.translate(item["text"])
        emotions = pipeline(translated_text)
        predicted_label = max(emotions[0], key=lambda x: x["score"])["label"]
        predictions.append(predicted_label)
    return predictions

true_labels = [item["label"] for item in test_data]

# BERT
start_time = time.time()
bert_predictions = get_predictions(emotion_pipeline_bert, translator_bert, test_data)
bert_time = time.time() - start_time

# RoBERTa
start_time = time.time()
roberta_predictions = get_predictions(emotion_pipeline_roberta, translator_roberta, test_data)
roberta_time = time.time() - start_time

print("\n=== Résultats pour BERT ===")
print(classification_report(true_labels, bert_predictions, zero_division=0))
print(f"\nTemps d'exécution : {bert_time:.2f} secondes")

print("\n=== Résultats pour RoBERTa ===")
print(classification_report(true_labels, roberta_predictions, zero_division=0))
print(f"\nTemps d'exécution : {roberta_time:.2f} secondes")

bert_cm = confusion_matrix(true_labels, bert_predictions, labels=list(set(true_labels)))
roberta_cm = confusion_matrix(true_labels, roberta_predictions, labels=list(set(true_labels)))

labels = sorted(list(set(true_labels)))

# Plot pour BERT
plt.figure(figsize=(6, 4))
sns.heatmap(bert_cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels)
plt.title("Matrice de confusion - BERT")
plt.xlabel("Prédiction")
plt.ylabel("Vérité")
plt.show()

# Plot pour RoBERTa
plt.figure(figsize=(6, 4))
sns.heatmap(roberta_cm, annot=True, fmt="d", cmap="Greens", xticklabels=labels, yticklabels=labels)
plt.title("Matrice de confusion - RoBERTa")
plt.xlabel("Prédiction")
plt.ylabel("Vérité")
plt.show()