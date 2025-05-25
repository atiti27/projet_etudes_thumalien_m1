# import os
# import re
# import requests
# import json
# import pandas as pd
# from datetime import datetime
# from typing import List, Dict, Optional, Tuple
# from dataclasses import dataclass
# from enum import Enum
# import difflib
# from sqlalchemy import select, insert, update, text
# from dotenv import load_dotenv
# from db import get_engine
# from create_tables import posts_table, fact_checks_table, metadata

# load_dotenv()

# class FactCheckRating(Enum):
#     """Classifications des évaluations de fact-checking"""
#     VRAI = "vrai"
#     FAUX = "faux"
#     PARTIELLEMENT_VRAI = "partiellement_vrai"
#     PARTIELLEMENT_FAUX = "partiellement_faux"
#     TROMPEUR = "trompeur"
#     NON_VERIFIE = "non_verifie"
#     INCERTAIN = "incertain"

# @dataclass
# class FactCheckResult:
#     """Résultat d'une vérification de fact-checking"""
#     claim_text: str
#     source_title: str
#     source_link: str
#     rating: str
#     source_site: str
#     similarity_score: float
#     confidence_level: str

# class FactCheckComparator:
#     """Classe principale pour comparer les tweets avec les bases de fact-checking"""
    
#     def __init__(self):
#         self.engine = get_engine()
#         self.api_key = os.getenv("FACTCHECK_API_KEY")
#         self.stop_words = {
#             "le", "la", "les", "de", "des", "du", "un", "une", "et", "à", "dans", "sur",
#             "pour", "par", "avec", "au", "aux", "ce", "ces", "se", "sa", "son", "que",
#             "qui", "dont", "où", "quand", "comment", "pourquoi", "mais", "ou", "car",
#             "donc", "or", "ni", "et", "puis", "alors", "ainsi", "aussi", "cependant",
#             "néanmoins", "toutefois", "pourtant", "en", "effet", "par", "exemple"
#         }
    
#     def extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
#         """Extrait les mots-clés d'un texte en filtrant les mots vides"""
#         # Nettoyer le texte
#         text = re.sub(r'[^\w\s]', ' ', text.lower())
#         words = re.findall(r'\b\w+\b', text)
        
#         # Filtrer les mots vides et les mots trop courts
#         keywords = [w for w in words if w not in self.stop_words and len(w) >= min_length]
        
#         # Retourner les mots-clés uniques en gardant l'ordre
#         seen = set()
#         unique_keywords = []
#         for word in keywords:
#             if word not in seen:
#                 seen.add(word)
#                 unique_keywords.append(word)
        
#         return unique_keywords[:10]  # Limiter à 10 mots-clés pour éviter les requêtes trop longues
    
#     def build_search_queries(self, keywords: List[str]) -> List[str]:
#         """Construit différentes requêtes de recherche à partir des mots-clés"""
#         if not keywords:
#             return []
        
#         queries = []
        
#         # Requête avec tous les mots-clés (AND)
#         if len(keywords) > 1:
#             queries.append(" ".join(keywords[:5]))  # Limiter à 5 mots pour AND
        
#         # Requête avec OR pour les mots-clés les plus importants
#         queries.append(" OR ".join(keywords[:3]))
        
#         # Requêtes individuelles pour les mots-clés les plus importants
#         for keyword in keywords[:2]:
#             queries.append(keyword)
        
#         return queries
    
#     def calculate_similarity(self, text1: str, text2: str) -> float:
#         """Calcule la similarité entre deux textes"""
#         if not text1 or not text2:
#             return 0.0
        
#         # Normaliser les textes
#         text1_norm = re.sub(r'[^\w\s]', '', text1.lower()).strip()
#         text2_norm = re.sub(r'[^\w\s]', '', text2.lower()).strip()
        
#         # Calculer la similarité avec difflib
#         similarity = difflib.SequenceMatcher(None, text1_norm, text2_norm).ratio()
        
#         # Calculer aussi la similarité des mots-clés
#         keywords1 = set(self.extract_keywords(text1))
#         keywords2 = set(self.extract_keywords(text2))
        
#         if keywords1 and keywords2:
#             keyword_similarity = len(keywords1.intersection(keywords2)) / len(keywords1.union(keywords2))
#             # Moyenne pondérée
#             similarity = 0.7 * similarity + 0.3 * keyword_similarity
        
#         return round(similarity, 3)
    
#     def normalize_rating(self, rating: str) -> str:
#         """Normalise les évaluations de fact-checking"""
#         if not rating:
#             return FactCheckRating.NON_VERIFIE.value
        
#         rating_lower = rating.lower()
        
#         # Mapping des évaluations communes
#         rating_mapping = {
#             "true": FactCheckRating.VRAI.value,
#             "vrai": FactCheckRating.VRAI.value,
#             "correct": FactCheckRating.VRAI.value,
#             "exact": FactCheckRating.VRAI.value,
            
#             "false": FactCheckRating.FAUX.value,
#             "faux": FactCheckRating.FAUX.value,
#             "incorrect": FactCheckRating.FAUX.value,
#             "erroné": FactCheckRating.FAUX.value,
            
#             "partly true": FactCheckRating.PARTIELLEMENT_VRAI.value,
#             "partiellement vrai": FactCheckRating.PARTIELLEMENT_VRAI.value,
#             "plutôt vrai": FactCheckRating.PARTIELLEMENT_VRAI.value,
#             "en partie vrai": FactCheckRating.PARTIELLEMENT_VRAI.value,
            
#             "partly false": FactCheckRating.PARTIELLEMENT_FAUX.value,
#             "partiellement faux": FactCheckRating.PARTIELLEMENT_FAUX.value,
#             "plutôt faux": FactCheckRating.PARTIELLEMENT_FAUX.value,
#             "en partie faux": FactCheckRating.PARTIELLEMENT_FAUX.value,
            
#             "misleading": FactCheckRating.TROMPEUR.value,
#             "trompeur": FactCheckRating.TROMPEUR.value,
#             "décontextualisé": FactCheckRating.TROMPEUR.value,
            
#             "unproven": FactCheckRating.INCERTAIN.value,
#             "uncertain": FactCheckRating.INCERTAIN.value,
#             "incertain": FactCheckRating.INCERTAIN.value,
#             "non prouvé": FactCheckRating.INCERTAIN.value,
#             "c'est plus compliqué": FactCheckRating.INCERTAIN.value
#         }
        
#         for key, value in rating_mapping.items():
#             if key in rating_lower:
#                 return value
        
#         return FactCheckRating.NON_VERIFIE.value
    
#     def determine_confidence_level(self, similarity_score: float, num_sources: int) -> str:
#         """Détermine le niveau de confiance basé sur la similarité et le nombre de sources"""
#         if similarity_score >= 0.8 and num_sources >= 2:
#             return "ÉLEVÉ"
#         elif similarity_score >= 0.6 and num_sources >= 1:
#             return "MOYEN"
#         elif similarity_score >= 0.4:
#             return "FAIBLE"
#         else:
#             return "TRÈS FAIBLE"
    
#     def search_fact_check_api(self, query: str, max_results: int = 5) -> List[Dict]:
#         """Recherche dans l'API Google Fact Check Tools"""
#         if not self.api_key:
#             print("⚠️  Clé API Fact Check manquante")
#             return []
        
#         url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
#         params = {
#             'query': query,
#             'languageCode': 'fr',
#             'key': self.api_key,
#             'pageSize': max_results
#         }
        
#         try:
#             response = requests.get(url, params=params, timeout=10)
#             if response.status_code == 200:
#                 data = response.json()
#                 return data.get("claims", [])
#             else:
#                 print(f"⚠️  Erreur API ({response.status_code}) pour la requête: {query}")
#                 return []
#         except requests.exceptions.RequestException as e:
#             print(f"⚠️  Erreur de connexion API: {e}")
#             return []
    
#     def process_fact_check_claims(self, claims: List[Dict], original_text: str) -> List[FactCheckResult]:
#         """Traite les résultats de l'API fact-checking"""
#         results = []
        
#         for claim in claims:
#             claim_text = claim.get("text", "")
#             claim_reviews = claim.get("claimReview", [])
            
#             if not claim_reviews:
#                 continue
            
#             # Calculer la similarité avec le texte original
#             similarity = self.calculate_similarity(original_text, claim_text)
            
#             # Ne garder que les résultats avec une similarité minimale
#             if similarity < 0.3:
#                 continue
            
#             for review in claim_reviews:
#                 publisher = review.get("publisher", {})
#                 rating_text = review.get("textualRating", "")
                
#                 result = FactCheckResult(
#                     claim_text=claim_text,
#                     source_title=review.get("title", ""),
#                     source_link=review.get("url", ""),
#                     rating=self.normalize_rating(rating_text),
#                     source_site=publisher.get("name", ""),
#                     similarity_score=similarity,
#                     confidence_level=self.determine_confidence_level(similarity, len(claim_reviews))
#                 )
                
#                 results.append(result)
        
#         # Trier par score de similarité décroissant
#         results.sort(key=lambda x: x.similarity_score, reverse=True)
#         return results[:3]  # Retourner les 3 meilleurs résultats
    
#     def compare_post_with_factcheck(self, post_id: int, content: str, title: str = "") -> List[FactCheckResult]:
#         """Compare un post avec les bases de fact-checking"""
#         print(f"\n🔍 Analyse du post #{post_id}")
        
#         # Combiner le titre et le contenu pour la recherche
#         search_text = f"{title} {content}".strip()
#         keywords = self.extract_keywords(search_text)
        
#         if not keywords:
#             print("❌ Aucun mot-clé extrait du post")
#             return []
        
#         print(f"🔤 Mots-clés extraits: {', '.join(keywords[:5])}")
        
#         # Générer les requêtes de recherche
#         queries = self.build_search_queries(keywords)
#         all_results = []
        
#         # Rechercher avec différentes requêtes
#         for query in queries:
#             print(f"🔎 Recherche avec: '{query}'")
#             claims = self.search_fact_check_api(query)
            
#             if claims:
#                 results = self.process_fact_check_claims(claims, search_text)
#                 all_results.extend(results)
        
#         # Éliminer les doublons et garder les meilleurs résultats
#         unique_results = {}
#         for result in all_results:
#             key = (result.claim_text, result.source_link)
#             if key not in unique_results or result.similarity_score > unique_results[key].similarity_score:
#                 unique_results[key] = result
        
#         final_results = list(unique_results.values())
#         final_results.sort(key=lambda x: x.similarity_score, reverse=True)
        
#         return final_results[:3]  # Retourner les 3 meilleurs résultats
    
#     def save_fact_check_results(self, post_id: int, results: List[FactCheckResult]):
#         """Sauvegarde les résultats de fact-checking en base de données"""
#         if not results:
#             return
        
#         with self.engine.begin() as conn:
#             # Supprimer les anciens résultats pour ce post
#             conn.execute(
#                 fact_checks_table.delete().where(fact_checks_table.c.post_id == post_id)
#             )
            
#             # Insérer les nouveaux résultats
#             for result in results:
#                 fact_check_data = {
#                     "post_id": post_id,
#                     "claim_id": f"similarity_{result.similarity_score}",
#                     "claim_text": result.claim_text,
#                     "source_title": result.source_title,
#                     "source_link": result.source_link,
#                     "source_excerpt": result.rating,
#                     "source_site": result.source_site
#                 }
                
#                 conn.execute(insert(fact_checks_table), fact_check_data)
        
#         print(f"💾 {len(results)} résultat(s) sauvegardé(s) pour le post #{post_id}")
    
#     def analyze_all_posts(self, limit: Optional[int] = None):
#         """Analyse tous les posts de la base de données"""
#         print("🚀 Démarrage de l'analyse fact-checking de tous les posts")
        
#         with self.engine.connect() as conn:
#             query = select(posts_table.c.id, posts_table.c.title, posts_table.c.content)
#             if limit:
#                 query = query.limit(limit)
            
#             result = conn.execute(query)
#             posts = result.fetchall()
        
#         print(f"📊 {len(posts)} post(s) à analyser")
        
#         summary = {
#             "total_posts": len(posts),
#             "posts_with_matches": 0,
#             "total_matches": 0,
#             "ratings_distribution": {}
#         }
        
#         for i, post in enumerate(posts, 1):
#             print(f"\n{'='*50}")
#             print(f"📝 Post {i}/{len(posts)} - ID: {post.id}")
            
#             results = self.compare_post_with_factcheck(
#                 post.id, 
#                 post.content or "", 
#                 post.title or ""
#             )
            
#             if results:
#                 summary["posts_with_matches"] += 1
#                 summary["total_matches"] += len(results)
                
#                 print(f"✅ {len(results)} correspondance(s) trouvée(s):")
#                 for j, result in enumerate(results, 1):
#                     print(f"  {j}. Similarité: {result.similarity_score:.1%}")
#                     print(f"     Évaluation: {result.rating.upper()}")
#                     print(f"     Source: {result.source_site}")
#                     print(f"     Confiance: {result.confidence_level}")
                    
#                     # Compter les évaluations
#                     rating = result.rating
#                     summary["ratings_distribution"][rating] = summary["ratings_distribution"].get(rating, 0) + 1
                
#                 # Sauvegarder les résultats
#                 self.save_fact_check_results(post.id, results)
#             else:
#                 print("❌ Aucune correspondance trouvée")
        
#         self.print_analysis_summary(summary)
    
#     def print_analysis_summary(self, summary: Dict):
#         """Affiche un résumé de l'analyse"""
#         print(f"\n{'='*60}")
#         print("📈 RÉSUMÉ DE L'ANALYSE FACT-CHECKING")
#         print(f"{'='*60}")
        
#         print(f"📊 Posts analysés: {summary['total_posts']}")
#         print(f"✅ Posts avec correspondances: {summary['posts_with_matches']}")
#         print(f"🎯 Taux de correspondance: {summary['posts_with_matches']/summary['total_posts']*100:.1f}%")
#         print(f"📋 Total des correspondances: {summary['total_matches']}")
        
#         if summary["ratings_distribution"]:
#             print(f"\n🏷️  DISTRIBUTION DES ÉVALUATIONS:")
#             for rating, count in sorted(summary["ratings_distribution"].items()):
#                 percentage = count / summary["total_matches"] * 100
#                 print(f"   {rating.upper().replace('_', ' ')}: {count} ({percentage:.1f}%)")
    
#     def generate_fact_check_report(self, output_file: str = "fact_check_report.json"):
#         """Génère un rapport détaillé des résultats de fact-checking"""
#         with self.engine.connect() as conn:
#             query = text("""
#                 SELECT p.id, p.title, p.content, p.author, p.publi_date,
#                        f.claim_text, f.source_title, f.source_link, 
#                        f.source_excerpt as rating, f.source_site
#                 FROM posts p
#                 LEFT JOIN fact_checks_sources f ON p.id = f.post_id
#                 ORDER BY p.id, f.id
#             """)
            
#             result = conn.execute(query)
#             rows = result.fetchall()
        
#         # Organiser les données par post
#         posts_data = {}
#         for row in rows:
#             post_id = row.id
#             if post_id not in posts_data:
#                 posts_data[post_id] = {
#                     "post_info": {
#                         "id": row.id,
#                         "title": row.title,
#                         "content": row.content[:200] + "..." if len(row.content or "") > 200 else row.content,
#                         "author": row.author,
#                         "publi_date": str(row.publi_date)
#                     },
#                     "fact_checks": []
#                 }
            
#             if row.claim_text:  # Il y a un fact-check associé
#                 posts_data[post_id]["fact_checks"].append({
#                     "claim_text": row.claim_text,
#                     "source_title": row.source_title,
#                     "source_link": row.source_link,
#                     "rating": row.rating,
#                     "source_site": row.source_site
#                 })
        
#         # Sauvegarder le rapport
#         report_data = {
#             "generated_at": datetime.now().isoformat(),
#             "total_posts": len(posts_data),
#             "posts_with_fact_checks": len([p for p in posts_data.values() if p["fact_checks"]]),
#             "posts": list(posts_data.values())
#         }
        
#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(report_data, f, ensure_ascii=False, indent=2)
        
#         print(f"📄 Rapport généré: {output_file}")
#         return report_data

# def main():
#     """Fonction principale"""
#     comparator = FactCheckComparator()
    
#     print("🎯 SYSTÈME DE COMPARAISON FACT-CHECKING")
#     print("=" * 50)
    
#     # Menu interactif
#     while True:
#         print("\n📋 Options disponibles:")
#         print("1. Analyser tous les posts")
#         print("2. Analyser un nombre limité de posts")
#         print("3. Analyser un post spécifique")
#         print("4. Générer un rapport détaillé")
#         print("5. Quitter")
        
#         choice = input("\n🔢 Votre choix (1-5): ").strip()
        
#         if choice == "1":
#             comparator.analyze_all_posts()
        
#         elif choice == "2":
#             try:
#                 limit = int(input("🔢 Nombre de posts à analyser: "))
#                 comparator.analyze_all_posts(limit=limit)
#             except ValueError:
#                 print("❌ Veuillez entrer un nombre valide")
        
#         elif choice == "3":
#             try:
#                 post_id = int(input("🔢 ID du post à analyser: "))
                
#                 # Récupérer le post
#                 with comparator.engine.connect() as conn:
#                     result = conn.execute(
#                         select(posts_table.c.title, posts_table.c.content)
#                         .where(posts_table.c.id == post_id)
#                     )
#                     post = result.fetchone()
                
#                 if post:
#                     results = comparator.compare_post_with_factcheck(
#                         post_id, post.content or "", post.title or ""
#                     )
#                     if results:
#                         comparator.save_fact_check_results(post_id, results)
#                     else:
#                         print("❌ Aucun résultat trouvé pour ce post")
#                 else:
#                     print("❌ Post non trouvé")
                    
#             except ValueError:
#                 print("❌ Veuillez entrer un ID valide")
        
#         elif choice == "4":
#             filename = input("📄 Nom du fichier de rapport (par défaut: fact_check_report.json): ").strip()
#             if not filename:
#                 filename = "fact_check_report.json"
#             comparator.generate_fact_check_report(filename)
        
#         elif choice == "5":
#             print("👋 Au revoir!")
#             break
        
#         else:
#             print("❌ Choix invalide, veuillez réessayer")

# if __name__ == "__main__":
#     main()


import os
import re
import requests
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import difflib
from sqlalchemy import select, insert, update, text
from dotenv import load_dotenv
from db import get_engine
from create_tables import posts_table, fact_checks_table, metadata

load_dotenv()

class FactCheckRating(Enum):
    """Classifications des évaluations de fact-checking"""
    VRAI = "vrai"
    FAUX = "faux"
    PARTIELLEMENT_VRAI = "partiellement_vrai"
    PARTIELLEMENT_FAUX = "partiellement_faux"
    TROMPEUR = "trompeur"
    NON_VERIFIE = "non_verifie"
    INCERTAIN = "incertain"

@dataclass
class FactCheckResult:
    """Résultat d'une vérification de fact-checking"""
    claim_text: str
    source_title: str
    source_link: str
    rating: str
    source_site: str
    similarity_score: float
    confidence_level: str

class FactCheckComparator:
    """Classe principale pour comparer les tweets avec les bases de fact-checking"""
    
    def __init__(self):
        self.engine = get_engine()
        self.api_key = os.getenv("FACTCHECK_API_KEY")
        
        # Créer les tables si elles n'existent pas
        self._ensure_tables_exist()
        
        self.stop_words = {
            "le", "la", "les", "de", "des", "du", "un", "une", "et", "à", "dans", "sur",
            "pour", "par", "avec", "au", "aux", "ce", "ces", "se", "sa", "son", "que",
            "qui", "dont", "où", "quand", "comment", "pourquoi", "mais", "ou", "car",
            "donc", "or", "ni", "et", "puis", "alors", "ainsi", "aussi", "cependant",
            "néanmoins", "toutefois", "pourtant", "en", "effet", "par", "exemple"
        }
    
    def _ensure_tables_exist(self):
        """Vérifie et crée les tables si nécessaire"""
        try:
            # Tenter de créer toutes les tables (ne fait rien si elles existent déjà)
            metadata.create_all(self.engine)
            print("✅ Tables vérifiées/créées avec succès")
        except Exception as e:
            print(f"⚠️  Erreur lors de la création des tables: {e}")
            print("🔧 Assurez-vous que la base de données est accessible")
    
    def extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """Extrait les mots-clés d'un texte en filtrant les mots vides"""
        # Nettoyer le texte
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = re.findall(r'\b\w+\b', text)
        
        # Filtrer les mots vides et les mots trop courts
        keywords = [w for w in words if w not in self.stop_words and len(w) >= min_length]
        
        # Retourner les mots-clés uniques en gardant l'ordre
        seen = set()
        unique_keywords = []
        for word in keywords:
            if word not in seen:
                seen.add(word)
                unique_keywords.append(word)
        
        return unique_keywords[:10]  # Limiter à 10 mots-clés pour éviter les requêtes trop longues
    
    def build_search_queries(self, keywords: List[str]) -> List[str]:
        """Construit différentes requêtes de recherche à partir des mots-clés"""
        if not keywords:
            return []
        
        queries = []
        
        # Requête avec tous les mots-clés (AND)
        if len(keywords) > 1:
            queries.append(" ".join(keywords[:5]))  # Limiter à 5 mots pour AND
        
        # Requête avec OR pour les mots-clés les plus importants
        queries.append(" OR ".join(keywords[:3]))
        
        # Requêtes individuelles pour les mots-clés les plus importants
        for keyword in keywords[:2]:
            queries.append(keyword)
        
        return queries
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcule la similarité entre deux textes"""
        if not text1 or not text2:
            return 0.0
        
        # Normaliser les textes
        text1_norm = re.sub(r'[^\w\s]', '', text1.lower()).strip()
        text2_norm = re.sub(r'[^\w\s]', '', text2.lower()).strip()
        
        # Calculer la similarité avec difflib
        similarity = difflib.SequenceMatcher(None, text1_norm, text2_norm).ratio()
        
        # Calculer aussi la similarité des mots-clés
        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))
        
        if keywords1 and keywords2:
            keyword_similarity = len(keywords1.intersection(keywords2)) / len(keywords1.union(keywords2))
            # Moyenne pondérée
            similarity = 0.7 * similarity + 0.3 * keyword_similarity
        
        return round(similarity, 3)
    
    def normalize_rating(self, rating: str) -> str:
        """Normalise les évaluations de fact-checking"""
        if not rating:
            return FactCheckRating.NON_VERIFIE.value
        
        rating_lower = rating.lower()
        
        # Mapping des évaluations communes
        rating_mapping = {
            "true": FactCheckRating.VRAI.value,
            "vrai": FactCheckRating.VRAI.value,
            "correct": FactCheckRating.VRAI.value,
            "exact": FactCheckRating.VRAI.value,
            
            "false": FactCheckRating.FAUX.value,
            "faux": FactCheckRating.FAUX.value,
            "incorrect": FactCheckRating.FAUX.value,
            "erroné": FactCheckRating.FAUX.value,
            
            "partly true": FactCheckRating.PARTIELLEMENT_VRAI.value,
            "partiellement vrai": FactCheckRating.PARTIELLEMENT_VRAI.value,
            "plutôt vrai": FactCheckRating.PARTIELLEMENT_VRAI.value,
            "en partie vrai": FactCheckRating.PARTIELLEMENT_VRAI.value,
            
            "partly false": FactCheckRating.PARTIELLEMENT_FAUX.value,
            "partiellement faux": FactCheckRating.PARTIELLEMENT_FAUX.value,
            "plutôt faux": FactCheckRating.PARTIELLEMENT_FAUX.value,
            "en partie faux": FactCheckRating.PARTIELLEMENT_FAUX.value,
            
            "misleading": FactCheckRating.TROMPEUR.value,
            "trompeur": FactCheckRating.TROMPEUR.value,
            "décontextualisé": FactCheckRating.TROMPEUR.value,
            
            "unproven": FactCheckRating.INCERTAIN.value,
            "uncertain": FactCheckRating.INCERTAIN.value,
            "incertain": FactCheckRating.INCERTAIN.value,
            "non prouvé": FactCheckRating.INCERTAIN.value,
            "c'est plus compliqué": FactCheckRating.INCERTAIN.value
        }
        
        for key, value in rating_mapping.items():
            if key in rating_lower:
                return value
        
        return FactCheckRating.NON_VERIFIE.value
    
    def determine_confidence_level(self, similarity_score: float, num_sources: int) -> str:
        """Détermine le niveau de confiance basé sur la similarité et le nombre de sources"""
        if similarity_score >= 0.8 and num_sources >= 2:
            return "ÉLEVÉ"
        elif similarity_score >= 0.6 and num_sources >= 1:
            return "MOYEN"
        elif similarity_score >= 0.4:
            return "FAIBLE"
        else:
            return "TRÈS FAIBLE"
    
    def search_fact_check_api(self, query: str, max_results: int = 5) -> List[Dict]:
        """Recherche dans l'API Google Fact Check Tools"""
        if not self.api_key:
            print("⚠️  Clé API Fact Check manquante")
            return []
        
        url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        params = {
            'query': query,
            'languageCode': 'fr',
            'key': self.api_key,
            'pageSize': max_results
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("claims", [])
            else:
                print(f"⚠️  Erreur API ({response.status_code}) pour la requête: {query}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Erreur de connexion API: {e}")
            return []
    
    def process_fact_check_claims(self, claims: List[Dict], original_text: str) -> List[FactCheckResult]:
        """Traite les résultats de l'API fact-checking"""
        results = []
        
        for claim in claims:
            claim_text = claim.get("text", "")
            claim_reviews = claim.get("claimReview", [])
            
            if not claim_reviews:
                continue
            
            # Calculer la similarité avec le texte original
            similarity = self.calculate_similarity(original_text, claim_text)
            
            # Ne garder que les résultats avec une similarité minimale
            if similarity < 0.3:
                continue
            
            for review in claim_reviews:
                publisher = review.get("publisher", {})
                rating_text = review.get("textualRating", "")
                
                result = FactCheckResult(
                    claim_text=claim_text,
                    source_title=review.get("title", ""),
                    source_link=review.get("url", ""),
                    rating=self.normalize_rating(rating_text),
                    source_site=publisher.get("name", ""),
                    similarity_score=similarity,
                    confidence_level=self.determine_confidence_level(similarity, len(claim_reviews))
                )
                
                results.append(result)
        
        # Trier par score de similarité décroissant
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:3]  # Retourner les 3 meilleurs résultats
    
    def compare_post_with_factcheck(self, post_id: int, content: str, title: str = "") -> List[FactCheckResult]:
        """Compare un post avec les bases de fact-checking"""
        print(f"\n🔍 Analyse du post #{post_id}")
        
        # Combiner le titre et le contenu pour la recherche
        search_text = f"{title} {content}".strip()
        keywords = self.extract_keywords(search_text)
        
        if not keywords:
            print("❌ Aucun mot-clé extrait du post")
            return []
        
        print(f"🔤 Mots-clés extraits: {', '.join(keywords[:5])}")
        
        # Générer les requêtes de recherche
        queries = self.build_search_queries(keywords)
        all_results = []
        
        # Rechercher avec différentes requêtes
        for query in queries:
            print(f"🔎 Recherche avec: '{query}'")
            claims = self.search_fact_check_api(query)
            
            if claims:
                results = self.process_fact_check_claims(claims, search_text)
                all_results.extend(results)
        
        # Éliminer les doublons et garder les meilleurs résultats
        unique_results = {}
        for result in all_results:
            key = (result.claim_text, result.source_link)
            if key not in unique_results or result.similarity_score > unique_results[key].similarity_score:
                unique_results[key] = result
        
        final_results = list(unique_results.values())
        final_results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return final_results[:3]  # Retourner les 3 meilleurs résultats
    
    def save_fact_check_results(self, post_id: int, results: List[FactCheckResult]):
        """Sauvegarde les résultats de fact-checking en base de données"""
        if not results:
            return
        
        with self.engine.begin() as conn:
            # Supprimer les anciens résultats pour ce post
            conn.execute(
                fact_checks_table.delete().where(fact_checks_table.c.post_id == post_id)
            )
            
            # Insérer les nouveaux résultats
            for result in results:
                fact_check_data = {
                    "post_id": post_id,
                    "claim_id": f"similarity_{result.similarity_score}",
                    "claim_text": result.claim_text,
                    "source_title": result.source_title,
                    "source_link": result.source_link,
                    "source_excerpt": result.rating,
                    "source_site": result.source_site
                }
                
                conn.execute(insert(fact_checks_table), fact_check_data)
        
        print(f"💾 {len(results)} résultat(s) sauvegardé(s) pour le post #{post_id}")
    
    def analyze_all_posts(self, limit: Optional[int] = None):
        """Analyse tous les posts de la base de données"""
        print("🚀 Démarrage de l'analyse fact-checking de tous les posts")
        
        with self.engine.connect() as conn:
            query = select(posts_table.c.id, posts_table.c.title, posts_table.c.content)
            if limit:
                query = query.limit(limit)
            
            result = conn.execute(query)
            posts = result.fetchall()
        
        print(f"📊 {len(posts)} post(s) à analyser")
        
        summary = {
            "total_posts": len(posts),
            "posts_with_matches": 0,
            "total_matches": 0,
            "ratings_distribution": {}
        }
        
        for i, post in enumerate(posts, 1):
            print(f"\n{'='*50}")
            print(f"📝 Post {i}/{len(posts)} - ID: {post.id}")
            
            results = self.compare_post_with_factcheck(
                post.id, 
                post.content or "", 
                post.title or ""
            )
            
            if results:
                summary["posts_with_matches"] += 1
                summary["total_matches"] += len(results)
                
                print(f"✅ {len(results)} correspondance(s) trouvée(s):")
                for j, result in enumerate(results, 1):
                    print(f"  {j}. Similarité: {result.similarity_score:.1%}")
                    print(f"     Évaluation: {result.rating.upper()}")
                    print(f"     Source: {result.source_site}")
                    print(f"     Confiance: {result.confidence_level}")
                    
                    # Compter les évaluations
                    rating = result.rating
                    summary["ratings_distribution"][rating] = summary["ratings_distribution"].get(rating, 0) + 1
                
                # Sauvegarder les résultats
                self.save_fact_check_results(post.id, results)
            else:
                print("❌ Aucune correspondance trouvée")
        
        self.print_analysis_summary(summary)
    
    def print_analysis_summary(self, summary: Dict):
        """Affiche un résumé de l'analyse"""
        print(f"\n{'='*60}")
        print("📈 RÉSUMÉ DE L'ANALYSE FACT-CHECKING")
        print(f"{'='*60}")
        
        print(f"📊 Posts analysés: {summary['total_posts']}")
        print(f"✅ Posts avec correspondances: {summary['posts_with_matches']}")
        print(f"🎯 Taux de correspondance: {summary['posts_with_matches']/summary['total_posts']*100:.1f}%")
        print(f"📋 Total des correspondances: {summary['total_matches']}")
        
        if summary["ratings_distribution"]:
            print(f"\n🏷️  DISTRIBUTION DES ÉVALUATIONS:")
            for rating, count in sorted(summary["ratings_distribution"].items()):
                percentage = count / summary["total_matches"] * 100
                print(f"   {rating.upper().replace('_', ' ')}: {count} ({percentage:.1f}%)")
    
    def generate_fact_check_report(self, output_file: str = "fact_check_report.json"):
        """Génère un rapport détaillé des résultats de fact-checking"""
        with self.engine.connect() as conn:
            query = text("""
                SELECT p.id, p.title, p.content, p.author, p.publi_date,
                       f.claim_text, f.source_title, f.source_link, 
                       f.source_excerpt as rating, f.source_site
                FROM posts p
                LEFT JOIN fact_checks_sources f ON p.id = f.post_id
                ORDER BY p.id, f.id
            """)
            
            result = conn.execute(query)
            rows = result.fetchall()
        
        # Organiser les données par post
        posts_data = {}
        for row in rows:
            post_id = row.id
            if post_id not in posts_data:
                posts_data[post_id] = {
                    "post_info": {
                        "id": row.id,
                        "title": row.title,
                        "content": row.content[:200] + "..." if len(row.content or "") > 200 else row.content,
                        "author": row.author,
                        "publi_date": str(row.publi_date)
                    },
                    "fact_checks": []
                }
            
            if row.claim_text:  # Il y a un fact-check associé
                posts_data[post_id]["fact_checks"].append({
                    "claim_text": row.claim_text,
                    "source_title": row.source_title,
                    "source_link": row.source_link,
                    "rating": row.rating,
                    "source_site": row.source_site
                })
        
        # Sauvegarder le rapport
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "total_posts": len(posts_data),
            "posts_with_fact_checks": len([p for p in posts_data.values() if p["fact_checks"]]),
            "posts": list(posts_data.values())
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"📄 Rapport généré: {output_file}")
        return report_data

def main():
    """Fonction principale"""
    print("🎯 SYSTÈME DE COMPARAISON FACT-CHECKING")
    print("=" * 50)
    
    try:
        comparator = FactCheckComparator()
    except Exception as e:
        print(f"❌ Erreur d'initialisation: {e}")
        print("🔧 Vérifiez votre configuration de base de données")
        return
    
    # Menu interactif
    while True:
        print("\n📋 Options disponibles:")
        print("1. Analyser tous les posts")
        print("2. Analyser un nombre limité de posts")
        print("3. Analyser un post spécifique")
        print("4. Générer un rapport détaillé")
        print("5. Quitter")
        
        choice = input("\n🔢 Votre choix (1-5): ").strip()
        
        if choice == "1":
            comparator.analyze_all_posts()
        
        elif choice == "2":
            try:
                limit = int(input("🔢 Nombre de posts à analyser: "))
                comparator.analyze_all_posts(limit=limit)
            except ValueError:
                print("❌ Veuillez entrer un nombre valide")
        
        elif choice == "3":
            try:
                post_id = int(input("🔢 ID du post à analyser: "))
                
                # Récupérer le post
                with comparator.engine.connect() as conn:
                    result = conn.execute(
                        select(posts_table.c.title, posts_table.c.content)
                        .where(posts_table.c.id == post_id)
                    )
                    post = result.fetchone()
                
                if post:
                    results = comparator.compare_post_with_factcheck(
                        post_id, post.content or "", post.title or ""
                    )
                    if results:
                        comparator.save_fact_check_results(post_id, results)
                    else:
                        print("❌ Aucun résultat trouvé pour ce post")
                else:
                    print("❌ Post non trouvé")
                    
            except ValueError:
                print("❌ Veuillez entrer un ID valide")
        
        elif choice == "4":
            filename = input("📄 Nom du fichier de rapport (par défaut: fact_check_report.json): ").strip()
            if not filename:
                filename = "fact_check_report.json"
            comparator.generate_fact_check_report(filename)
        
        elif choice == "5":
            print("👋 Au revoir!")
            break
        
        else:
            print("❌ Choix invalide, veuillez réessayer")

if __name__ == "__main__":
    main()