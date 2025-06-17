import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from sqlalchemy import text
from db import get_engine
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

# Configuration des graphiques
plt.style.use('seaborn-v0_8')
sns.set_palette("Set2")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

class AutomaticReportsGenerator:
    """Générateur de rapports automatiques pour l'analyse de fiabilité"""
    
    def __init__(self):
        self.engine = get_engine()
        self.report_date = datetime.now()
        self.output_dir = "reports"
        self.create_output_directory()
    
    def create_output_directory(self):
        """Crée le répertoire de sortie pour les rapports"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"📁 Répertoire '{self.output_dir}' créé")
    
    def get_analysis_data(self):
        """Récupère toutes les données d'analyse depuis la base"""
        with self.engine.connect() as connection:
            query = text("""
                SELECT 
                    p.id,
                    p.title,
                    p.content,
                    p.author,
                    p.publi_date,
                    p.nbr_like,
                    p.nbr_comment,
                    p.nbr_repost,
                    p.hashtags,
                    cra.content_category,
                    cra.content_confidence,
                    cra.is_fake_news,
                    cra.fake_news_confidence,
                    cra.content_reliability_score,
                    cra.has_fact_check,
                    cra.fact_check_rating,
                    cra.fact_check_source,
                    cra.external_reliability_score,
                    cra.global_reliability_score,
                    cra.final_category,
                    cra.confidence_level,
                    cra.created_at as analysis_date
                FROM comprehensive_reliability_analysis cra
                JOIN posts p ON cra.post_id = p.id
                ORDER BY p.publi_date DESC
            """)
            
            result = connection.execute(query)
            df = pd.DataFrame([dict(row._mapping) for row in result])
            
            if not df.empty:
                df['publi_date'] = pd.to_datetime(df['publi_date'])
                df['analysis_date'] = pd.to_datetime(df['analysis_date'])
            
            return df
    
    def generate_executive_summary(self, df):
        """Génère un résumé exécutif"""
        if df.empty:
            return {}
        
        total_posts = len(df)
        fake_news_count = len(df[df['is_fake_news'] == 1])
        reliable_count = len(df[df['final_category'] == 'Fiable'])
        fact_checked_count = len(df[df['has_fact_check'] == True])
        avg_reliability = df['global_reliability_score'].mean()
        
        # Tendance sur 7 derniers jours
        week_ago = datetime.now() - timedelta(days=7)
        recent_posts = df[df['publi_date'] >= week_ago]
        recent_fake_rate = len(recent_posts[recent_posts['is_fake_news'] == 1]) / len(recent_posts) if len(recent_posts) > 0 else 0
        
        return {
            'total_posts': total_posts,
            'fake_news_count': fake_news_count,
            'fake_news_rate': (fake_news_count / total_posts) * 100,
            'reliable_count': reliable_count,
            'reliable_rate': (reliable_count / total_posts) * 100,
            'fact_checked_count': fact_checked_count,
            'fact_check_rate': (fact_checked_count / total_posts) * 100,
            'avg_reliability': avg_reliability,
            'recent_posts_count': len(recent_posts),
            'recent_fake_rate': recent_fake_rate * 100
        }
    
    def create_reliability_distribution_chart(self, df, save_path):
        """Graphique de distribution des scores de fiabilité"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Distribution des scores
        ax1.hist(df['global_reliability_score'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(df['global_reliability_score'].mean(), color='red', linestyle='--', 
                   label=f'Moyenne: {df["global_reliability_score"].mean():.1f}')
        ax1.set_xlabel('Score de Fiabilité')
        ax1.set_ylabel('Nombre de Posts')
        ax1.set_title('Distribution des Scores de Fiabilité')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Répartition par catégorie
        category_counts = df['final_category'].value_counts()
        colors = ['#ff6b6b', '#feca57', '#48dbfb', '#0abde3', '#10ac84', '#5f27cd']
        ax2.pie(category_counts.values, labels=category_counts.index, autopct='%1.1f%%', 
               colors=colors[:len(category_counts)])
        ax2.set_title('Répartition par Catégorie de Fiabilité')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_temporal_analysis_chart(self, df, save_path):
        """Analyse temporelle de la fiabilité"""
        if df.empty:
            return
        
        # Grouper par jour
        df_daily = df.groupby(df['publi_date'].dt.date).agg({
            'global_reliability_score': 'mean',
            'is_fake_news': 'sum',
            'id': 'count'
        }).reset_index()
        df_daily.columns = ['date', 'avg_reliability', 'fake_count', 'total_count']
        df_daily['fake_rate'] = (df_daily['fake_count'] / df_daily['total_count']) * 100
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))
        
        # Score de fiabilité moyen par jour
        ax1.plot(df_daily['date'], df_daily['avg_reliability'], marker='o', linewidth=2)
        ax1.set_ylabel('Score Moyen de Fiabilité')
        ax1.set_title('Évolution du Score de Fiabilité dans le Temps')
        ax1.grid(True, alpha=0.3)
        
        # Taux de fake news par jour
        ax2.bar(df_daily['date'], df_daily['fake_rate'], alpha=0.7, color='salmon')
        ax2.set_ylabel('Taux de Fake News (%)')
        ax2.set_title('Évolution du Taux de Fake News dans le Temps')
        ax2.grid(True, alpha=0.3)
        
        # Volume de posts par jour
        ax3.bar(df_daily['date'], df_daily['total_count'], alpha=0.7, color='lightblue')
        ax3.set_ylabel('Nombre de Posts')
        ax3.set_xlabel('Date')
        ax3.set_title('Volume de Posts Analysés par Jour')
        ax3.grid(True, alpha=0.3)
        
        # Formater les dates sur l'axe x
        for ax in [ax1, ax2, ax3]:
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_author_analysis_chart(self, df, save_path):
        """Analyse par auteur"""
        if df.empty:
            return
        
        # Top auteurs par volume et fiabilité
        author_stats = df.groupby('author').agg({
            'global_reliability_score': ['mean', 'count'],
            'is_fake_news': 'sum'
        }).reset_index()
        
        author_stats.columns = ['author', 'avg_reliability', 'post_count', 'fake_count']
        author_stats['fake_rate'] = (author_stats['fake_count'] / author_stats['post_count']) * 100
        author_stats = author_stats[author_stats['post_count'] >= 2]  # Auteurs avec au moins 2 posts
        
        if author_stats.empty:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
        
        # Top 10 auteurs les plus fiables
        top_reliable = author_stats.nlargest(10, 'avg_reliability')
        ax1.barh(range(len(top_reliable)), top_reliable['avg_reliability'])
        ax1.set_yticks(range(len(top_reliable)))
        ax1.set_yticklabels([f"{author[:20]}..." if len(author) > 20 else author 
                           for author in top_reliable['author']])
        ax1.set_xlabel('Score Moyen de Fiabilité')
        ax1.set_title('Top 10 Auteurs les Plus Fiables')
        ax1.grid(True, alpha=0.3)
        
        # Relation volume vs fiabilité
        scatter = ax2.scatter(author_stats['post_count'], author_stats['avg_reliability'], 
                            c=author_stats['fake_rate'], cmap='RdYlBu_r', alpha=0.7, s=100)
        ax2.set_xlabel('Nombre de Posts')
        ax2.set_ylabel('Score Moyen de Fiabilité')
        ax2.set_title('Relation Volume vs Fiabilité par Auteur')
        ax2.grid(True, alpha=0.3)
        
        # Colorbar pour le taux de fake news
        cbar = plt.colorbar(scatter, ax=ax2)
        cbar.set_label('Taux de Fake News (%)')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_engagement_analysis_chart(self, df, save_path):
        """Analyse de l'engagement vs fiabilité"""
        if df.empty:
            return
        
        # Calculer l'engagement total
        df['total_engagement'] = df['nbr_like'] + df['nbr_comment'] + df['nbr_repost']
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Fiabilité vs Likes
        ax1.scatter(df['nbr_like'], df['global_reliability_score'], alpha=0.6, c='blue')
        ax1.set_xlabel('Nombre de Likes')
        ax1.set_ylabel('Score de Fiabilité')
        ax1.set_title('Fiabilité vs Likes')
        ax1.grid(True, alpha=0.3)
        
        # Fiabilité vs Commentaires
        ax2.scatter(df['nbr_comment'], df['global_reliability_score'], alpha=0.6, c='green')
        ax2.set_xlabel('Nombre de Commentaires')
        ax2.set_ylabel('Score de Fiabilité')
        ax2.set_title('Fiabilité vs Commentaires')
        ax2.grid(True, alpha=0.3)
        
        # Fiabilité vs Reposts
        ax3.scatter(df['nbr_repost'], df['global_reliability_score'], alpha=0.6, c='red')
        ax3.set_xlabel('Nombre de Reposts')
        ax3.set_ylabel('Score de Fiabilité')
        ax3.set_title('Fiabilité vs Reposts')
        ax3.grid(True, alpha=0.3)
        
        # Engagement total par catégorie
        engagement_by_category = df.groupby('final_category')['total_engagement'].mean().sort_values(ascending=True)
        ax4.barh(range(len(engagement_by_category)), engagement_by_category.values)
        ax4.set_yticks(range(len(engagement_by_category)))
        ax4.set_yticklabels(engagement_by_category.index)
        ax4.set_xlabel('Engagement Moyen')
        ax4.set_title('Engagement Moyen par Catégorie')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_fact_check_analysis_chart(self, df, save_path):
        """Analyse des fact-checks"""
        fact_checked = df[df['has_fact_check'] == True]
        
        if fact_checked.empty:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Sources de fact-check
        source_counts = fact_checked['fact_check_source'].value_counts()
        ax1.pie(source_counts.values, labels=source_counts.index, autopct='%1.1f%%')
        ax1.set_title('Répartition des Sources de Fact-Check')
        
        # Fiabilité selon les ratings de fact-check
        rating_reliability = fact_checked.groupby('fact_check_rating')['global_reliability_score'].mean().sort_values()
        ax2.barh(range(len(rating_reliability)), rating_reliability.values)
        ax2.set_yticks(range(len(rating_reliability)))
        ax2.set_yticklabels(rating_reliability.index)
        ax2.set_xlabel('Score Moyen de Fiabilité')
        ax2.set_title('Score de Fiabilité par Rating de Fact-Check')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_detailed_table(self, df):
        """Génère un tableau détaillé des posts"""
        if df.empty:
            return pd.DataFrame()
        
        # Sélectionner et formater les colonnes importantes
        detailed_table = df[['id', 'title', 'author', 'publi_date', 'final_category', 
                           'global_reliability_score', 'is_fake_news', 'fact_check_rating',
                           'fact_check_source', 'nbr_like', 'nbr_comment', 'nbr_repost']].copy()
        
        # Formater les colonnes
        detailed_table['publi_date'] = detailed_table['publi_date'].dt.strftime('%Y-%m-%d %H:%M')
        detailed_table['title'] = detailed_table['title'].apply(lambda x: x[:50] + '...' if len(str(x)) > 50 else x)
        detailed_table['is_fake_news'] = detailed_table['is_fake_news'].map({1: 'Oui', 0: 'Non'})
        detailed_table['global_reliability_score'] = detailed_table['global_reliability_score'].round(1)
        
        # Renommer les colonnes pour le rapport
        detailed_table.columns = ['ID', 'Titre', 'Auteur', 'Date Publication', 'Catégorie',
                                'Score Fiabilité', 'Fake News', 'Rating Fact-Check',
                                'Source Fact-Check', 'Likes', 'Commentaires', 'Reposts']
        
        return detailed_table
    
    def generate_html_report(self, df, summary, charts_paths):
        """Génère un rapport HTML complet"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Rapport d'Analyse de Fiabilité - {self.report_date.strftime('%d/%m/%Y')}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; border-bottom: 3px solid #007bff; padding-bottom: 20px; }}
                .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .metric {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
                .metric h3 {{ margin: 0 0 10px 0; font-size: 2.5em; }}
                .metric p {{ margin: 0; font-size: 1.1em; }}
                .chart {{ margin: 30px 0; text-align: center; }}
                .chart img {{ max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                .table-container {{ overflow-x: auto; margin: 30px 0; }}
                table {{ width: 100%; border-collapse: collapse; background-color: white; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; font-weight: bold; color: #495057; }}
                tr:hover {{ background-color: #f8f9fa; }}
                .fake-news {{ background-color: #ffe6e6 !important; }}
                .reliable {{ background-color: #e6ffe6 !important; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔍 Rapport d'Analyse de Fiabilité</h1>
                    <p>Généré le {self.report_date.strftime('%d/%m/%Y à %H:%M')}</p>
                </div>
                
                <div class="summary">
                    <div class="metric">
                        <h3>{summary.get('total_posts', 0)}</h3>
                        <p>Posts Analysés</p>
                    </div>
                    <div class="metric">
                        <h3>{summary.get('fake_news_rate', 0):.1f}%</h3>
                        <p>Taux de Fake News</p>
                    </div>
                    <div class="metric">
                        <h3>{summary.get('reliable_rate', 0):.1f}%</h3>
                        <p>Posts Fiables</p>
                    </div>
                    <div class="metric">
                        <h3>{summary.get('avg_reliability', 0):.1f}</h3>
                        <p>Score Moyen</p>
                    </div>
                    <div class="metric">
                        <h3>{summary.get('fact_check_rate', 0):.1f}%</h3>
                        <p>Fact-Checkés</p>
                    </div>
                </div>
        """
        
        # Ajouter les graphiques
        for chart_name, chart_path in charts_paths.items():
            if os.path.exists(chart_path):
                html_content += f"""
                <div class="chart">
                    <h2>{chart_name}</h2>
                    <img src="{os.path.basename(chart_path)}" alt="{chart_name}">
                </div>
                """
        
        # Ajouter le tableau détaillé
        detailed_table = self.generate_detailed_table(df)
        if not detailed_table.empty:
            html_content += """
                <div class="table-container">
                    <h2>📊 Tableau Détaillé des Posts</h2>
                    <table>
            """
            
            # En-têtes
            html_content += "<tr>"
            for col in detailed_table.columns:
                html_content += f"<th>{col}</th>"
            html_content += "</tr>"
            
            # Données
            for _, row in detailed_table.iterrows():
                row_class = ""
                if row['Fake News'] == 'Oui':
                    row_class = "fake-news"
                elif row['Catégorie'] == 'Fiable':
                    row_class = "reliable"
                
                html_content += f'<tr class="{row_class}">'
                for value in row:
                    html_content += f"<td>{value if pd.notna(value) else '-'}</td>"
                html_content += "</tr>"
            
            html_content += "</table></div>"
        
        # Footer
        html_content += f"""
                <div class="footer">
                    <p>Rapport généré automatiquement par le système d'analyse de fiabilité</p>
                    <p>Données basées sur {summary.get('total_posts', 0)} posts analysés avec RoBERTa et fact-checks externes</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def generate_complete_report(self):
        """Génère un rapport complet avec tous les éléments"""
        print("📊 GÉNÉRATION DU RAPPORT AUTOMATIQUE")
        print("=" * 50)
        
        # 1. Récupérer les données
        print("📥 Récupération des données...")
        df = self.get_analysis_data()
        
        if df.empty:
            print("❌ Aucune donnée trouvée. Exécutez d'abord l'analyse des posts.")
            return
        
        print(f"✅ {len(df)} posts trouvés")
        
        # 2. Générer le résumé exécutif
        print("📋 Génération du résumé exécutif...")
        summary = self.generate_executive_summary(df)
        
        # 3. Créer les graphiques
        print("📈 Création des graphiques...")
        timestamp = self.report_date.strftime("%Y%m%d_%H%M%S")
        
        charts_paths = {
            "Distribution de la Fiabilité": f"{self.output_dir}/reliability_distribution_{timestamp}.png",
            "Analyse Temporelle": f"{self.output_dir}/temporal_analysis_{timestamp}.png",
            "Analyse par Auteur": f"{self.output_dir}/author_analysis_{timestamp}.png",
            "Engagement vs Fiabilité": f"{self.output_dir}/engagement_analysis_{timestamp}.png",
            "Analyse des Fact-Checks": f"{self.output_dir}/factcheck_analysis_{timestamp}.png"
        }
        
        try:
            self.create_reliability_distribution_chart(df, charts_paths["Distribution de la Fiabilité"])
            self.create_temporal_analysis_chart(df, charts_paths["Analyse Temporelle"])
            self.create_author_analysis_chart(df, charts_paths["Analyse par Auteur"])
            self.create_engagement_analysis_chart(df, charts_paths["Engagement vs Fiabilité"])
            self.create_fact_check_analysis_chart(df, charts_paths["Analyse des Fact-Checks"])
            print("✅ Graphiques créés")
        except Exception as e:
            print(f"⚠️ Erreur lors de la création des graphiques: {e}")
        
        # 4. Générer le rapport HTML
        print("🌐 Génération du rapport HTML...")
        html_content = self.generate_html_report(df, summary, charts_paths)
        
        html_path = f"{self.output_dir}/rapport_fiabilite_{timestamp}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 5. Exporter les données en CSV
        print("💾 Export des données en CSV...")
        detailed_table = self.generate_detailed_table(df)
        csv_path = f"{self.output_dir}/donnees_analyse_{timestamp}.csv"
        detailed_table.to_csv(csv_path, index=False, encoding='utf-8')
        
        # 6. Rapport textuel console
        print("\n" + "="*60)
        print("           RÉSUMÉ EXÉCUTIF")
        print("="*60)
        print(f"📊 Total posts analysés: {summary['total_posts']}")
        print(f"🚨 Fake news détectées: {summary['fake_news_count']} ({summary['fake_news_rate']:.1f}%)")
        print(f"✅ Posts fiables: {summary['reliable_count']} ({summary['reliable_rate']:.1f}%)")
        print(f"🔍 Posts fact-checkés: {summary['fact_checked_count']} ({summary['fact_check_rate']:.1f}%)")
        print(f"📈 Score moyen de fiabilité: {summary['avg_reliability']:.1f}/100")
        
        if summary['recent_posts_count'] > 0:
            print(f"📅 Posts récents (7 derniers jours): {summary['recent_posts_count']}")
            print(f"🎯 Taux de fake news récent: {summary['recent_fake_rate']:.1f}%")
        
        print(f"\n📄 Fichiers générés:")
        print(f"   • Rapport HTML: {html_path}")
        print(f"   • Données CSV: {csv_path}")
        print(f"   • Graphiques: {len(charts_paths)} fichiers PNG")
        
        print(f"\n🌐 Ouvrez le rapport HTML dans votre navigateur:")
        print(f"   {os.path.abspath(html_path)}")
        
        return {
            'html_report': html_path,
            'csv_data': csv_path,
            'charts': charts_paths,
            'summary': summary
        }

def main():
    generator = AutomaticReportsGenerator()
    generator.generate_complete_report()

if __name__ == "__main__":
    main()