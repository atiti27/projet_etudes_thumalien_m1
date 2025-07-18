from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from sqlalchemy import text
from db.db_connection import get_engine
from deep_translator import GoogleTranslator
from db.create_tables import comprehensive_analysis_table, metadata

load_dotenv()

# Modèle RoBERTa pour classification multi-classes
model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
classification_pipeline = pipeline("text-classification", model=model, tokenizer=tokenizer)

# Modèle RoBERTa spécialisé pour la détection de fake news
fake_news_model = "hamzab/roberta-fake-news-classification"
fake_tokenizer = AutoTokenizer.from_pretrained(fake_news_model)
fake_model = AutoModelForSequenceClassification.from_pretrained(fake_news_model)
fake_news_pipeline = pipeline("text-classification", model=fake_model, tokenizer=fake_tokenizer)

engine = get_engine()
translator = GoogleTranslator(source='fr', target='en')

def classify_content(text):
    """Classifie le contenu en catégories avec RoBERTa"""
    try:
        translated_text = translator.translate(text)
        result = classification_pipeline(translated_text)
        
        # Mapping des labels vers nos catégories
        label = result[0]['label']
        confidence = result[0]['score']
        
        # Conversion vers nos catégories métier
        category_mapping = {
            'LABEL_0': 'Opinion négative',
            'LABEL_1': 'Opinion neutre', 
            'LABEL_2': 'Opinion positive',
            'negative': 'Opinion négative',
            'neutral': 'Information factuelle',
            'positive': 'Opinion positive'
        }
        
        category = category_mapping.get(label, 'Information générale')
        
        return category, confidence
        
    except Exception as e:
        print(f"Erreur classification contenu: {e}")
        return "Indéterminé", 0.0

def detect_fake_news(text):
    """Détecte les fake news avec RoBERTa"""
    try:
        translated_text = translator.translate(text)
        result = fake_news_pipeline(translated_text)
        
        prediction = result[0]
        label = prediction['label'].upper()
        confidence = prediction['score']
        
        is_fake = 1 if label == "FAKE" else 0
        
        return is_fake, confidence
        
    except Exception as e:
        print(f"Erreur détection fake news: {e}")
        return 0, 0.0

def calculate_content_reliability_score(category, fake_confidence, content_confidence):
    """Calcule le score de fiabilité basé sur le contenu"""
    base_score = 50  # Score de base
    
    # Ajustement selon la catégorie
    category_scores = {
        'Information factuelle': 20,
        'Information générale': 10,
        'Opinion neutre': 5,
        'Opinion positive': 0,
        'Opinion négative': -5,
        'Indéterminé': -10
    }
    
    category_adjustment = category_scores.get(category, 0)
    
    # Ajustement selon la détection fake news
    fake_adjustment = -30 if fake_confidence > 0.7 else 0
    
    # Ajustement selon la confiance dans la classification
    confidence_adjustment = (content_confidence - 0.5) * 20
    
    score = base_score + category_adjustment + fake_adjustment + confidence_adjustment
    return max(0, min(100, score))  # Limiter entre 0 et 100

def get_external_fact_check_data(post_id):
    """Récupère les données de fact-checking externes déjà collectées"""
    with engine.connect() as connection:
        # Récupérer les fact-checks depuis la table fact_checks
        fact_checks = connection.execute(text("""
            SELECT source_excerpt, source_site, source_link
            FROM fact_checks_sources 
            WHERE post_id = :post_id
            ORDER BY id
            LIMIT 1
        """), {"post_id": post_id}).fetchone()
        
        if fact_checks:
            return {
                "rating": fact_checks.source_excerpt,
                "source": fact_checks.source_site,
                "url": fact_checks.source_link
            }
        return None

def calculate_external_reliability_score(fact_check_data):
    """Calcule le score de fiabilité basé sur les sources externes"""
    if not fact_check_data:
        return 50  # Score neutre si pas de fact-check
    
    rating = fact_check_data.get("rating", "").lower()
    
    # Scores plus nuancés et précis
    rating_scores = {
        'vrai': 95, 'true': 95, 'vérifié': 95, 'correct': 95,
        'plutôt vrai': 80, 'mostly true': 80, 'largement vrai': 80,
        'en partie vrai': 65, 'partly true': 65, 'partiellement vrai': 65,
        'c\'est plus compliqué': 50, 'mixed': 50, 'nuancé': 50,
        'plutôt faux': 25, 'mostly false': 25, 'largement faux': 25,
        'faux': 5, 'false': 5, 'fake': 5, 'mensonge': 5,
        'trompeur': 15, 'misleading': 15, 'désinformation': 10
    }
    
    for key, score in rating_scores.items():
        if key in rating:
            return score
    
    return 50  # Score par défaut

def calculate_global_reliability_score(content_score, external_score, has_fact_check, fact_check_source=""):
    """Calcule le score global de fiabilité avec pondération intelligente"""
    if not has_fact_check:
        return content_score
    
    # Sources très fiables (pondération 80% externe, 20% contenu)
    high_trust_sources = ["franceinfo", "afp factuel", "liberation", "le monde", "reuters", "bbc"]
    
    # Sources moyennement fiables (pondération 60% externe, 40% contenu)
    medium_trust_sources = ["tf1 info", "20 minutes", "figaro", "ouest-france"]
    
    source_lower = fact_check_source.lower()
    
    if any(trusted in source_lower for trusted in high_trust_sources):
        # Priorité forte aux sources très fiables
        return (external_score * 0.8) + (content_score * 0.2)
    elif any(medium in source_lower for medium in medium_trust_sources):
        # Pondération équilibrée pour sources moyennes
        return (external_score * 0.6) + (content_score * 0.4)
    else:
        # Sources inconnues : équilibre 50/50
        return (external_score * 0.5) + (content_score * 0.5)

def determine_final_category(global_score, is_fake_news, fake_confidence, has_fact_check, external_score, fact_check_source=""):
    """
    Détermine la catégorie finale avec logique corrigée et seuils optimisés
    Basé sur l'analyse d'évaluation qui montre une performance optimale au seuil 40
    """
    
    # Sources très fiables - priorité absolue
    high_trust_sources = ["franceinfo", "afp factuel", "liberation", "le monde", "reuters", "bbc"]
    source_lower = fact_check_source.lower()
    
    # 1. Si on a un fact-check de source très fiable, on lui fait confiance
    if has_fact_check and any(trusted in source_lower for trusted in high_trust_sources):
        if external_score >= 80:
            return "Fiable"
        elif external_score >= 60:
            return "Plutôt fiable"
        elif external_score <= 30:
            return "Fake News"
        else:
            return "Douteux"
    
    # 2. Si l'IA détecte clairement du fake news avec haute confiance
    if is_fake_news == 1 and fake_confidence > 0.8:
        return "Fake News"
    
    # 3. Si l'IA dit que ce n'est PAS fake, on doit être cohérent
    if is_fake_news == 0:
        # Seuils optimisés basés sur l'évaluation (seuil optimal = 40)
        if global_score >= 60:  # Abaissé de 70 à 60
            return "Fiable"
        elif global_score >= 40:  # Abaissé de 50 à 40 (seuil optimal)
            return "Plutôt fiable"
        elif global_score >= 25:  # Abaissé de 30 à 25
            return "Douteux"
        else:
            return "Peu fiable"
    
    # 4. Cas où is_fake_news == 1 mais confiance faible
    if is_fake_news == 1:
        if fake_confidence > 0.6:
            return "Fake News"
        elif global_score < 30:  # Abaissé de 40 à 30
            return "Peu fiable"
        else:
            return "Douteux"
    
    # 5. Cas par défaut : seuils optimisés pour le score global
    if global_score >= 70:      # Abaissé de 80 à 70
        return "Fiable"
    elif global_score >= 50:    # Abaissé de 60 à 50
        return "Plutôt fiable"
    elif global_score >= 40:    # Seuil optimal identifié
        return "Douteux"
    elif global_score >= 20:    # Inchangé
        return "Peu fiable"
    else:
        return "Non fiable"

def determine_confidence_level(content_conf, fake_conf, has_fact_check):
    """Détermine le niveau de confiance"""
    avg_conf = (content_conf + fake_conf) / 2
    
    if has_fact_check and avg_conf > 0.8:
        return "Très élevée"
    elif avg_conf > 0.7:
        return "Élevée"
    elif avg_conf > 0.5:
        return "Moyenne"
    else:
        return "Faible"

def comprehensive_analysis(text, post_id):
    """Analyse complète d'un texte en utilisant les fact-checks existants"""
    
    # 1. Classification du contenu
    category, content_confidence = classify_content(text)
    
    # 2. Détection fake news
    is_fake, fake_confidence = detect_fake_news(text)
    
    # 3. Score de fiabilité du contenu
    content_score = calculate_content_reliability_score(category, fake_confidence, content_confidence)
    
    # 4. Récupérer les fact-checks existants (au lieu de les rechercher)
    fact_check_data = get_external_fact_check_data(post_id)
    has_fact_check = fact_check_data is not None
    external_score = calculate_external_reliability_score(fact_check_data)
    
    # 5. Score global
    global_score = calculate_global_reliability_score(content_score, external_score, has_fact_check, 
                                                     fact_check_data.get("source", "") if fact_check_data else "")
    
    # 6. Catégorie finale (avec logique corrigée)
    final_category = determine_final_category(global_score, is_fake, fake_confidence, has_fact_check, 
                                            external_score, fact_check_data.get("source", "") if fact_check_data else "")
    
    # 7. Niveau de confiance
    confidence_level = determine_confidence_level(content_confidence, fake_confidence, has_fact_check)
    
    return {
        "post_id": post_id,
        "content_category": category,
        "content_confidence": round(content_confidence, 4),
        "is_fake_news": is_fake,
        "fake_news_confidence": round(fake_confidence, 4),
        "content_reliability_score": round(content_score, 2),
        "has_fact_check": has_fact_check,
        "fact_check_rating": fact_check_data.get("rating", "") if fact_check_data else "",
        "fact_check_source": fact_check_data.get("source", "") if fact_check_data else "",
        "external_reliability_score": round(external_score, 2),
        "global_reliability_score": round(global_score, 2),
        "final_category": final_category,
        "confidence_level": confidence_level
    }

def analyze_posts_comprehensive():
    """Analyse complète de tous les posts non traités"""
    with engine.connect() as connection:
        # Sélectionner seulement les posts qui n'ont pas encore été analysés
        posts_table = connection.execute(text("""
            SELECT p.id, p.title, p.content 
            FROM posts p
            LEFT JOIN comprehensive_reliability_analysis cra 
            ON p.id = cra.post_id
            WHERE cra.post_id IS NULL
            ORDER BY p.id
        """)).fetchall()

        print(f"Nombre de posts à analyser: {len(posts_table)}")

        for post in posts_table:
            post_id, title, content = post
            try:
                # Combiner titre et contenu
                full_text = f"{title} {content}" if title and title != "None" else content
                
                print(f"\n--- Analyse du post ID {post_id} ---")
                analysis_data = comprehensive_analysis(full_text, post_id)
                
                connection.execute(comprehensive_analysis_table.insert(), analysis_data)
                connection.commit()
                
                print(f"✅ Catégorie: {analysis_data['final_category']}")
                print(f"   Score global: {analysis_data['global_reliability_score']:.1f}%")
                print(f"   IA détecte fake: {'Oui' if analysis_data['is_fake_news'] else 'Non'}")
                print(f"   Confiance: {analysis_data['confidence_level']}")
                print(f"   Fact-check externe: {'Oui' if analysis_data['has_fact_check'] else 'Non'}")
                
            except Exception as e:
                print(f"❌ Erreur pour le post ID {post_id}: {e}")
                continue

def fix_existing_inconsistencies():
    """Corrige les incohérences dans les données existantes"""
    print("\n🔧 CORRECTION DES INCOHÉRENCES EXISTANTES")
    print("-" * 50)
    
    with engine.connect() as connection:
        # Récupérer toutes les analyses existantes
        analyses = connection.execute(text("""
            SELECT id, post_id, global_reliability_score, is_fake_news, 
                   fake_news_confidence, has_fact_check, external_reliability_score,
                   fact_check_source, final_category
            FROM comprehensive_reliability_analysis
        """)).fetchall()
        
        corrections_made = 0
        
        for analysis in analyses:
            # Recalculer la catégorie avec la logique corrigée
            new_category = determine_final_category(
                analysis.global_reliability_score,
                analysis.is_fake_news,
                analysis.fake_news_confidence,
                analysis.has_fact_check,
                analysis.external_reliability_score,
                analysis.fact_check_source or ""
            )
            
            # Si différent, mettre à jour
            if new_category != analysis.final_category:
                connection.execute(text("""
                    UPDATE comprehensive_reliability_analysis 
                    SET final_category = :new_category
                    WHERE id = :analysis_id
                """), {
                    "new_category": new_category,
                    "analysis_id": analysis.id
                })
                
                print(f"✅ Post #{analysis.post_id}: '{analysis.final_category}' → '{new_category}'")
                corrections_made += 1
        
        connection.commit()
        print(f"\n🔧 {corrections_made} corrections appliquées")

def generate_synthetic_report():
    """Génère un rapport synthétique des analyses"""
    with engine.connect() as connection:
        # Statistiques générales
        stats = connection.execute(text("""
            SELECT 
                COUNT(*) as total_posts,
                AVG(global_reliability_score) as avg_reliability,
                COUNT(CASE WHEN final_category = 'Fake News' THEN 1 END) as fake_news_count,
                COUNT(CASE WHEN final_category = 'Fiable' THEN 1 END) as reliable_count,
                COUNT(CASE WHEN has_fact_check = true THEN 1 END) as fact_checked_count,
                COUNT(CASE WHEN is_fake_news = 1 AND final_category = 'Fake News' THEN 1 END) as consistent_fake,
                COUNT(CASE WHEN is_fake_news = 0 AND final_category != 'Fake News' THEN 1 END) as consistent_real
            FROM comprehensive_reliability_analysis
        """)).fetchone()
        
        if stats and stats.total_posts > 0:
            print("\n" + "="*60)
            print("           RAPPORT SYNTHÉTIQUE DE FIABILITÉ")
            print("="*60)
            
            print(f"\n📊 STATISTIQUES GÉNÉRALES:")
            print(f"   • Total posts analysés: {stats.total_posts}")
            print(f"   • Score de fiabilité moyen: {stats.avg_reliability:.1f}%")
            print(f"   • Posts fact-checkés: {stats.fact_checked_count} ({stats.fact_checked_count/stats.total_posts*100:.1f}%)")
            
            # Vérification de cohérence
            consistency_rate = ((stats.consistent_fake + stats.consistent_real) / stats.total_posts) * 100
            print(f"   • Cohérence IA/Catégorie: {consistency_rate:.1f}%")
            
            print(f"\n🎯 RÉPARTITION PAR CATÉGORIE:")
            print(f"   • Fake News détectées: {stats.fake_news_count}")
            print(f"   • Informations fiables: {stats.reliable_count}")
            print(f"   • Autres catégories: {stats.total_posts - stats.fake_news_count - stats.reliable_count}")
            
            # Distribution par catégorie
            categories = connection.execute(text("""
                SELECT final_category, COUNT(*) as count,
                       AVG(global_reliability_score) as avg_score
                FROM comprehensive_reliability_analysis
                GROUP BY final_category
                ORDER BY count DESC
            """)).fetchall()
            
            print(f"\n📈 DÉTAIL PAR CATÉGORIE:")
            for cat in categories:
                print(f"   • {cat.final_category}: {cat.count} posts (score moyen: {cat.avg_score:.1f}%)")
            
            # Posts les plus problématiques
            print(f"\n⚠️  TOP 5 POSTS LES PLUS PROBLÉMATIQUES:")
            problematic = connection.execute(text("""
                SELECT p.title, cra.global_reliability_score, cra.final_category, cra.is_fake_news
                FROM comprehensive_reliability_analysis cra
                JOIN posts p ON cra.post_id = p.id
                WHERE cra.global_reliability_score < 50
                ORDER BY cra.global_reliability_score ASC
                LIMIT 5
            """)).fetchall()
            
            for i, post in enumerate(problematic, 1):
                title = post.title if post.title != "None" else "Sans titre"
                fake_status = "IA: Fake" if post.is_fake_news else "IA: Real"
                print(f"   {i}. {title[:50]}... ({post.final_category}: {post.global_reliability_score:.1f}%, {fake_status})")
            
            print("\n" + "="*60)

def analyze_specific_post(post_id):
    """Analyse un post spécifique pour la détection de fake news"""
    with engine.connect() as connection:
        # Récupérer le post
        post = connection.execute(text("""
            SELECT title, content FROM posts WHERE id = :post_id
        """), {"post_id": post_id}).fetchone()
        
        if not post:
            print(f"Post avec ID {post_id} non trouvé.")
            return
        
        # Vérifier s'il a déjà été analysé
        existing = connection.execute(text("""
            SELECT * FROM comprehensive_reliability_analysis WHERE post_id = :post_id
        """), {"post_id": post_id}).fetchone()
        
        if existing:
            print(f"Post déjà analysé:")
            print(f"Catégorie: {existing.final_category}")
            print(f"Score global: {existing.global_reliability_score:.1f}%")
            print(f"Confiance: {existing.confidence_level}")
            return
        
        # Analyser le post
        full_text = f"{post.title} {post.content}" if post.title and post.title != "None" else post.content
        analysis_data = comprehensive_analysis(full_text, post_id)
        
        # Sauvegarder le résultat
        connection.execute(comprehensive_analysis_table.insert(), analysis_data)
        connection.commit()
        
        print(f"Analyse terminée pour le post ID {post_id}")
        print(f"Catégorie: {analysis_data['final_category']}")
        print(f"Score global: {analysis_data['global_reliability_score']:.1f}%")

if __name__ == "__main__":
    print("🔍 ANALYSE COMPLÈTE DE FIABILITÉ AVEC ROBERTA")
    print("Fonctionnalités: Classification, Détection fake news, Utilisation des fact-checks existants")
    
    # Créer la table si elle n'existe pas
    print("\n📋 Vérification/création des tables...")
    metadata.create_all(engine)
    print("✅ Tables prêtes")
    
    # Message d'information sur la complémentarité
    print("\n💡 Ce script utilise les fact-checks déjà collectés par get_fact_checking_datas.py")
    print("   Assurez-vous d'avoir exécuté get_fact_checking_datas.py au préalable.")
    
    # Corriger les incohérences existantes
    fix_existing_inconsistencies()
    
    # Lancer l'analyse complète
    analyze_posts_comprehensive()
    
    # Générer le rapport
    generate_synthetic_report()