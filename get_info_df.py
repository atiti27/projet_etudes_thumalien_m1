import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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
    categorical_columns = df.select_dtypes(include=['object']).columns

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

    plt.figure(figsize=(14, 10))
    for i, col in enumerate(categorical_columns):
        plt.subplot(3, 2, i+1)
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

    # Matrice de corrélation
    plt.figure(figsize=(12, 8))
    sns.heatmap(df[numerical_columns].corr(), annot=True, fmt=".2f", cmap='coolwarm', square=True)
    plt.title('Matrice de corrélation')
    plt.show()
    
if __name__ == "__main__":

    # Exemple de données
    data = [
        {
            "title": "Example Title",
            "content": "Example content with some text.",
            "author": "John Doe",
            "publi_date": "2023-10-01",
            "link": "https://example.com",
            "nbr_like": 10,
            "nbr_comment": 5,
            "nbr_repost": 2,
            "hashtags": "#example #test",
        },
        {
            "title": "Another Title",
            "content": "Another piece of content.",
            "author": "Bob Brown",
            "publi_date": "2023-10-04",
            "link": "https://example.com/another",
            "nbr_like": 20,
            "nbr_comment": 10,
            "nbr_repost": 5,
            "hashtags": "#another #test",
        },
        {
            "title": "Third Title",
            "content": "Third content example.",
            "author": "Charlie Black",
            "publi_date": "2023-10-05",
            "link": "https://example.com/third",
            "nbr_like": 30,
            "nbr_comment": 15,
            "nbr_repost": 7,
            "hashtags": "#third #test",
        }
    ]

    df = pd.DataFrame(data)
    get_info_df(df)
    display_variable_distribution(df)