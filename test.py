from db import get_engine

engine = get_engine()

try:
    with engine.connect() as connection:
        print("Connexion réussie à la base de données !")
except Exception as e:
    print(f"Erreur de connexion ou de création de tables: {e}")