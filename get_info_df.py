import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import text
from db import get_engine


def transform_into_df(data, columns):
    return pd.DataFrame(data, columns=columns)

def get_info_df(df):
    pd.set_option('display.max_columns', None)
    print("Dimensions du DataFrame :", df.shape)
    print("\nPremières lignes du DataFrame :")
    print(df.head())
    print("\nInformations sur les colonnes:")
    print(df.info())
    print("\nVérications des valeurs manquantes:")
    print(df.isnull().sum())
    print("\nStatistiques descriptives des colonnes numériques:")
    print(df.describe())

def display_variable_distribution(df):
    """
    Affiche la distribution des variables du DataFrame
    """

    numerical_columns = df.select_dtypes(include=['int64', 'float64']).columns
    categorical_columns = df[["author", "hashtags"]]

    df[numerical_columns].hist(figsize=(15, 10), bins=30)
    plt.suptitle('Distribution des variables numériques')
    plt.show()

    plt.figure(figsize=(15, 5))
    for i, col in enumerate(numerical_columns):
        plt.subplot(1, 4, i+1)
        sns.boxplot(y=df[col])
        plt.title(f'Boxplot de {col}')
        plt.ylabel('')
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(15, 5))
    sns.boxplot(data=df[numerical_columns])
    plt.title('Boxplot des variables numériques')
    plt.show()

    plt.figure(figsize=(12, 8))
    for i, col in enumerate(categorical_columns):
        plt.subplot(2, 1, i+1)
        if df[col].nunique() > 10:
            order = df[col].value_counts().index[:10]
            sns.countplot(data=df, x=col, order=order)
        else:
            sns.countplot(data=df, x=col)
        plt.title(f'Distribution de {col}')
        plt.ylabel('Nombre de posts')
        plt.xlabel('')
    plt.tight_layout()
    plt.show()

    # Analyse temporelle
    df['publi_date'] = pd.to_datetime(df['publi_date'])
    df.set_index('publi_date').resample('ME')[['nbr_like', 'nbr_comment', 'nbr_repost']].sum().plot()
    plt.title('Évolution mensuelle des interactions')
    plt.show()

    # Matrice de corrélation
    plt.figure(figsize=(12, 8))
    sns.heatmap(df[numerical_columns].corr(), annot=True, fmt=".2f", cmap='coolwarm', square=True)
    plt.title('Matrice de corrélation')
    plt.show()
    
if __name__ == "__main__":

    engine = get_engine()

    # Récupérer les posts de la base de données
    with engine.connect() as connection:
        posts_table = connection.execute(text("""
            SELECT title, content, author, publi_date, link, nbr_like, nbr_comment, nbr_repost, hashtags
            FROM posts p
            ORDER BY p.id
        """)).fetchall()
        columns = ["title", "content", "author", "publi_date", "link", "nbr_like", "nbr_comment", "nbr_repost", "hashtags"]
        data = [{col: row[i] for i, col in enumerate(columns)} for row in posts_table]
        df = transform_into_df(data, columns)

        if df.empty:
            print("Aucun post trouvé dans la base de données.")
            exit()

        get_info_df(df)
        display_variable_distribution(df)