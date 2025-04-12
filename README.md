# **Détection des Fake News de Tweets: Lutte contre la désinformation**

## **Présentation de Thumalien et du projet**

Thumalien est un journal impliqué dans la lutte contre la désinformation, alliant une expertise journalistique dans la déconstruction des contenus numériques.

Dans le cadre de son engagement à atteindre cet objectif, Thumalien lance un projet innovant visant à renforcer ses capacités d'analyse d'informations. Le but de ce projet est de développer un outil d'analyse automatisé, capable d'identifier et de classer les tweets en provenance de Bluesky en fonction de leur probabilité d'être des fake-news. En s'appuyant sur des techniques de traitement du langage naturel (NLP) et d'algorithmes de machine learning, Thumalien aspire à améliorer la fiabilité, la rapidité et la précision des analyses tout en sensibilisant le public aux enjeux de la désinformation.

Ce guide utilisateur vous accompagnera tout au long du projet, en fournissant des instructions détaillées sur l'utilisation des outils développés.

## Guide d'utilisation de la solution technologique

### Installation

Pour lancer le projet, assurer vous d'être à la racine du projet `projet_etudes_thumalien`. Il faut avant tout installer les packages correspondants. Nous avons déjà mis à disposition les librairies requises dans le fichier `requirements.txt`. Pour leurs installations, il suffit de lancer la commande suivante:
```
pip install -r requirements.txt
```

D'autres librairies sont dépendantes de celles listées dans le fichier `requirements.txt`. Si vous n'avez pas PyTorch, installez le avec la commande suivante (pour Windows)
```
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
