import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve,
    precision_recall_curve, average_precision_score, matthews_corrcoef
)
from sqlalchemy import text
from db.db_connection import get_engine
import warnings
warnings.filterwarnings('ignore')

# Configuration pour les graphiques
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class FakeNewsEvaluator:
    def __init__(self):
        self.engine = get_engine()
        
    def create_ground_truth_dataset(self):
        """
        Crée un dataset de vérité terrain basé sur les fact-checks externes
        Les sources fiables (AFP, Franceinfo, etc.) servent de référence
        """
        with self.engine.connect() as connection:
            # Récupérer les données avec fact-checks de sources fiables
            query = text("""
                SELECT 
                    cra.post_id,
                    cra.is_fake_news,
                    cra.fake_news_confidence,
                    cra.final_category,
                    cra.global_reliability_score,
                    cra.fact_check_rating,
                    cra.fact_check_source,
                    cra.has_fact_check,
                    p.title,
                    p.content
                FROM comprehensive_reliability_analysis cra
                JOIN posts p ON cra.post_id = p.id
                WHERE cra.has_fact_check = true
                AND cra.fact_check_source IS NOT NULL
                AND cra.fact_check_source != ''
            """)
            
            results = connection.execute(query).fetchall()
            
            if not results:
                print("❌ Aucune donnée avec fact-checks trouvée.")
                return None
            
            # Convertir en DataFrame
            df = pd.DataFrame([dict(row._mapping) for row in results])
            
            # Créer les labels de vérité terrain basés sur les fact-checks
            df['ground_truth'] = df['fact_check_rating'].apply(self._rating_to_binary)
            
            # Filtrer seulement les cas où on a une vérité terrain claire
            df = df[df['ground_truth'].notna()].reset_index(drop=True)
            
            print(f"✅ Dataset créé avec {len(df)} échantillons étiquetés")
            return df
    
    def _rating_to_binary(self, rating):
        """Convertit les ratings de fact-check en labels binaires"""
        if pd.isna(rating) or rating == "":
            return None
            
        rating_lower = str(rating).lower()
        
        # Labels "Fake" (0)
        fake_keywords = ['faux', 'false', 'fake', 'mensonge', 'trompeur', 'misleading', 
                        'désinformation', 'plutôt faux', 'mostly false', 'largement faux']
        
        # Labels "Real" (1) 
        real_keywords = ['vrai', 'true', 'vérifié', 'correct', 'plutôt vrai', 
                        'mostly true', 'largement vrai', 'en partie vrai', 'partly true']
        
        for keyword in fake_keywords:
            if keyword in rating_lower:
                return 0  # Fake
        
        for keyword in real_keywords:
            if keyword in rating_lower:
                return 1  # Real
        
        return None  # Incertain
    
    def evaluate_binary_classification(self, df):
        """Évalue la classification binaire (fake vs real)"""
        y_true = df['ground_truth']
        y_pred = 1 - df['is_fake_news']  # Inverser car is_fake_news: 1=fake, 0=real
        y_scores = 1 - df['fake_news_confidence']  # Scores de probabilité
        
        # Métriques de base
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, average='binary')
        recall = recall_score(y_true, y_pred, average='binary')
        f1 = f1_score(y_true, y_pred, average='binary')
        
        # Métriques avancées
        try:
            auc_roc = roc_auc_score(y_true, y_scores)
        except:
            auc_roc = np.nan
            
        mcc = matthews_corrcoef(y_true, y_pred)
        
        # Matrice de confusion
        cm = confusion_matrix(y_true, y_pred)
        
        results = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'auc_roc': auc_roc,
            'matthews_corr': mcc,
            'confusion_matrix': cm,
            'classification_report': classification_report(y_true, y_pred, 
                                                         target_names=['Fake', 'Real'])
        }
        
        return results, y_true, y_pred, y_scores
    
    def evaluate_multiclass_classification(self, df):
        """Évalue la classification multi-classes"""
        # Mapper les catégories vers des codes numériques
        category_mapping = {
            'Fake News': 0,
            'Non fiable': 1,
            'Peu fiable': 2,
            'Douteux': 3,
            'Plutôt fiable': 4,
            'Fiable': 5
        }
        
        df['category_code'] = df['final_category'].map(category_mapping)
        df['ground_truth_category'] = df['ground_truth'].map({0: 0, 1: 5})  # Fake->0, Real->5
        
        # Filtrer les catégories valides
        valid_mask = df['category_code'].notna() & df['ground_truth_category'].notna()
        df_valid = df[valid_mask]
        
        if len(df_valid) == 0:
            return None
        
        y_true = df_valid['ground_truth_category']
        y_pred = df_valid['category_code']
        
        # Métriques multi-classes
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, average='weighted')
        recall = recall_score(y_true, y_pred, average='weighted')
        f1 = f1_score(y_true, y_pred, average='weighted')
        
        cm = confusion_matrix(y_true, y_pred)
        
        results = {
            'accuracy': accuracy,
            'precision_weighted': precision,
            'recall_weighted': recall,
            'f1_weighted': f1,
            'confusion_matrix': cm,
            'classification_report': classification_report(y_true, y_pred)
        }
        
        return results, y_true, y_pred
    
    def evaluate_score_based_classification(self, df):
        """Évalue en utilisant les scores de fiabilité comme seuils"""
        results = {}
        
        # Tester différents seuils de score
        thresholds = [30, 40, 50, 60, 70, 80]
        
        for threshold in thresholds:
            # Prédiction basée sur le seuil : score >= threshold = Real (1), sinon Fake (0)
            y_pred_threshold = (df['global_reliability_score'] >= threshold).astype(int)
            
            accuracy = accuracy_score(df['ground_truth'], y_pred_threshold)
            precision = precision_score(df['ground_truth'], y_pred_threshold, average='binary')
            recall = recall_score(df['ground_truth'], y_pred_threshold, average='binary')
            f1 = f1_score(df['ground_truth'], y_pred_threshold, average='binary')
            
            results[f'threshold_{threshold}'] = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1
            }
        
        return results
    
    def plot_confusion_matrix(self, cm, title, labels=None):
        """Affiche une matrice de confusion"""
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=labels, yticklabels=labels)
        plt.title(f'Matrice de Confusion - {title}')
        plt.xlabel('Prédictions')
        plt.ylabel('Vérité Terrain')
        plt.tight_layout()
        plt.show()
    
    def plot_roc_curve(self, y_true, y_scores, auc_score):
        """Affiche la courbe ROC"""
        fpr, tpr, _ = roc_curve(y_true, y_scores)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, linewidth=2, label=f'ROC Curve (AUC = {auc_score:.3f})')
        plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random Classifier')
        plt.xlabel('Taux de Faux Positifs')
        plt.ylabel('Taux de Vrais Positifs')
        plt.title('Courbe ROC - Détection de Fake News')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
    
    def plot_precision_recall_curve(self, y_true, y_scores):
        """Affiche la courbe Précision-Rappel"""
        precision, recall, _ = precision_recall_curve(y_true, y_scores)
        avg_precision = average_precision_score(y_true, y_scores)
        
        plt.figure(figsize=(8, 6))
        plt.plot(recall, precision, linewidth=2, 
                label=f'Courbe P-R (AP = {avg_precision:.3f})')
        plt.xlabel('Rappel')
        plt.ylabel('Précision')
        plt.title('Courbe Précision-Rappel - Détection de Fake News')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
    
    def plot_threshold_analysis(self, threshold_results):
        """Affiche l'analyse des seuils"""
        thresholds = []
        metrics = {'accuracy': [], 'precision': [], 'recall': [], 'f1_score': []}
        
        for key, values in threshold_results.items():
            threshold = int(key.split('_')[1])
            thresholds.append(threshold)
            for metric, value in values.items():
                metrics[metric].append(value)
        
        plt.figure(figsize=(12, 8))
        for metric, values in metrics.items():
            plt.plot(thresholds, values, marker='o', linewidth=2, label=metric.capitalize())
        
        plt.xlabel('Seuil de Score de Fiabilité')
        plt.ylabel('Score de Métrique')
        plt.title('Analyse des Seuils - Performance des Métriques')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
    
    def generate_evaluation_report(self):
        """Génère un rapport complet d'évaluation"""
        print("🔍 ÉVALUATION COMPLÈTE DU SYSTÈME DE DÉTECTION DE FAKE NEWS")
        print("=" * 70)
        
        # 1. Créer le dataset d'évaluation
        print("\n📊 Création du dataset d'évaluation...")
        df = self.create_ground_truth_dataset()
        
        if df is None or len(df) == 0:
            print("❌ Impossible de créer le dataset d'évaluation")
            return
        
        print(f"Dataset créé avec {len(df)} échantillons")
        print(f"Répartition: {sum(df['ground_truth'])} vrais, {len(df) - sum(df['ground_truth'])} fake")
        
        # 2. Évaluation binaire
        print("\n🎯 ÉVALUATION CLASSIFICATION BINAIRE (Fake vs Real)")
        print("-" * 50)
        
        binary_results, y_true, y_pred, y_scores = self.evaluate_binary_classification(df)
        
        print(f"Exactitude (Accuracy): {binary_results['accuracy']:.3f}")
        print(f"Précision: {binary_results['precision']:.3f}")
        print(f"Rappel: {binary_results['recall']:.3f}")
        print(f"Score F1: {binary_results['f1_score']:.3f}")
        print(f"AUC-ROC: {binary_results['auc_roc']:.3f}")
        print(f"Corrélation de Matthews: {binary_results['matthews_corr']:.3f}")
        
        print("\nRapport de classification détaillé:")
        print(binary_results['classification_report'])
        
        # 3. Visualisations
        print("\n📈 Génération des graphiques...")
        
        # Matrice de confusion
        self.plot_confusion_matrix(binary_results['confusion_matrix'], 
                                  "Classification Binaire", ['Fake', 'Real'])
        
        # Courbe ROC
        if not np.isnan(binary_results['auc_roc']):
            self.plot_roc_curve(y_true, y_scores, binary_results['auc_roc'])
            self.plot_precision_recall_curve(y_true, y_scores)
        
        # 4. Évaluation multi-classes
        print("\n🌈 ÉVALUATION CLASSIFICATION MULTI-CLASSES")
        print("-" * 50)
        
        multiclass_results = self.evaluate_multiclass_classification(df)
        if multiclass_results:
            results, y_true_multi, y_pred_multi = multiclass_results
            print(f"Exactitude: {results['accuracy']:.3f}")
            print(f"Précision pondérée: {results['precision_weighted']:.3f}")
            print(f"Rappel pondéré: {results['recall_weighted']:.3f}")
            print(f"Score F1 pondéré: {results['f1_weighted']:.3f}")
        
        # 5. Analyse des seuils
        print("\n⚖️ ANALYSE DES SEUILS DE SCORES")
        print("-" * 50)
        
        threshold_results = self.evaluate_score_based_classification(df)
        
        print("Performance selon différents seuils:")
        for threshold, metrics in threshold_results.items():
            print(f"\nSeuil {threshold.split('_')[1]}:")
            print(f"  Exactitude: {metrics['accuracy']:.3f}")
            print(f"  Précision: {metrics['precision']:.3f}")
            print(f"  Rappel: {metrics['recall']:.3f}")
            print(f"  F1-Score: {metrics['f1_score']:.3f}")
        
        # Graphique des seuils
        self.plot_threshold_analysis(threshold_results)
        
        # 6. Recommandations
        print("\n💡 RECOMMANDATIONS")
        print("-" * 50)
        
        best_f1_threshold = max(threshold_results.items(), 
                              key=lambda x: x[1]['f1_score'])
        
        print(f"• Meilleur seuil pour F1-Score: {best_f1_threshold[0].split('_')[1]} "
              f"(F1: {best_f1_threshold[1]['f1_score']:.3f})")
        
        if binary_results['precision'] > binary_results['recall']:
            print("• Le système privilégie la précision (peu de faux positifs)")
            print("• Recommandation: Ajuster pour améliorer le rappel si nécessaire")
        else:
            print("• Le système privilégie le rappel (détecte plus de fake news)")
            print("• Recommandation: Ajuster pour améliorer la précision si nécessaire")
        
        print(f"\n✅ Évaluation terminée ! Performance globale: {binary_results['f1_score']:.1%}")

def main():
    evaluator = FakeNewsEvaluator()
    evaluator.generate_evaluation_report()

if __name__ == "__main__":
    main()