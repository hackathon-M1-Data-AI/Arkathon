# Arkathon - Générateur d'Art Expressif

## 🎨 Présentation de l'équipe

- **BERGER Nolan** - Développeur Backend et Data Engineer
- **AGNILA Sofourath** - Data IA
- **BANCEL Valentin** - Développeur Web, IA Data et DevOps
- **SANOKO Sada** - Data Engineer
- **GUEYE SECK Awa Coumba** - Master en Data Engineer : manipulation, analyses et traitement de données

## 📝 Description du projet

Ce projet génère des images abstraites expressives à partir de fichiers CSV contenant des paramètres numériques. Le programme utilise ces données pour créer des compositions artistiques uniques avec différents types de formes (blob, stroke, splatter, spiral, wave, cloud), chacune influencée par les valeurs des colonnes du CSV.

Le générateur transforme des données brutes en art visuel en mappant chaque ligne du CSV vers un élément graphique dont l'apparence est contrôlée par les paramètres numériques.

## �� Structure du fichier d'entrée attendue

Le fichier CSV doit contenir les colonnes suivantes :

- **shape** : Type de forme à dessiner (`blob`, `stroke`,`splatter`,`spiral`,`wave`,`cloud`)
- **z** : Ordre de superposition des éléments (optionnel)
- **Colonnes numériques** : Les colonnes suivantes contiennent des valeurs numériques qui contrôlent l'apparence visuelle

### Mapping des paramètres visuels

| Rang numérique (0-based) | Paramètre visuel piloté | Effet dans l'image |
|---------------------------|-------------------------|---------------------|
| 0 | x (position horizontale) | Décale l'élément vers la gauche/droite (avec des marges internes) |
| 1 | y (position verticale) | Décale l'élément vers le haut/bas |
| 2 | size | Taille globale des gestes (rayon des "blob", longueur des "strokes", étendue des "splatter") |
| 3 | angle (0–360°) | Orientation des traits et direction des éclaboussures |
| 4 | thickness | Épaisseur des "strokes" (et un peu la présence visuelle) |
| 5 | vigor (énergie) | Jitter/irrégularité des traits + nombre/ampleur des gouttes ("splatter") |
| 6 | curveX | Courbure latérale du "stroke" (contrôle la forme de l'arche du trait) |
| 7 | curveY | Courbure verticale du "stroke" |
| 8 | spiral turns / wave freq | Nombre de tours pour "spiral" (2-6) / Fréquence pour "wave" |
| 9 | ry factor | Coefficient de rayon vertical (peu utilisé) |
| 10 | — | Non utilisé directement (mais peut influencer l'échelle de normalisation) |
| 11 | — | Non utilisé directement (idem) |

**Note importante** : Les deux dernières colonnes du CSV (rangs 10 et 11) ne changent pas beaucoup les résultats visuels.

### Formes acceptées

Le programme reconnaît six types de formes dans la colonne `shape` :

#### 🔵 **`blob`**
- **Description** : Formes organiques rondes avec des anneaux semi-transparents
- **Caractéristiques** : 3-6 anneaux concentriques, variations aléatoires du rayon
- **Meilleur usage** : Éléments doux et organiques, zones de couleur diffuses

#### ➰ **`stroke`**
- **Description** : Traits courbes avec contrôle de courbure (courbe de Bézier)
- **Caractéristiques** : Contrôle de la courbure via curveX et curveY, effet main levée
- **Meilleur usage** : Lignes expressives, gestes calligraphiques

#### 💥 **`splatter`**
- **Description** : Éclaboussures directionnelles avec particules
- **Caractéristiques** : 60-140 particules selon le paramètre vigor, distribution conique
- **Meilleur usage** : Effets dynamiques, explosions de couleur

#### 🌀 **`spiral`**
- **Description** : Spirales organiques avec variations de rayon
- **Caractéristiques** : 2-6 tours configurables, épaisseur décroissante, variations sinusoïdales
- **Meilleur usage** : Mouvements circulaires, énergie tourbillonnante

#### 🌊 **`wave`**
- **Description** : Motifs d'ondes fluides concentriques
- **Caractéristiques** : 3-8 ondes par forme, fréquences variables, formes fermées
- **Meilleur usage** : Flux liquides, ondulations organiques, textures aquatiques

#### ☁️ **`cloud`**
- **Description** : Nuages de particules avec distribution gaussienne
- **Caractéristiques** : 40-120 particules, clustering naturel, transparence dégradée
- **Meilleur usage** : Textures diffuses, effets atmosphériques, masses organiques


## 🚀 Instructions complètes pour la récupération et le lancement du programme

### Prérequis

- Python 3.12 ou supérieur
- pip ou uv (gestionnaire de paquets Python)  

### Installation

1. **Cloner le dépôt**
```bash
git clone https://github.com/hackathon-M1-Data-AI/Arkathon.git
cd Arkathon
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

Ou avec uv (gestionnaire de paquets moderne) :
```bash
uv sync
```

### Utilisation

#### Syntaxe de base
```bash
python generator.py <fichier_csv> [fichier_sortie.png]
```

#### Exemples d'utilisation

Générer une image à partir d'un CSV avec nom de sortie par défaut :
```bash
python generator.py radical_100.csv
```

Générer une image avec nom personnalisé :
```bash
python generator.py radical_500.csv mon_artwork.png
```

Tester avec les différents fichiers fournis :
```bash
python generator.py radical_10.csv test_10.png
python generator.py radical_100.csv test_100.png
python generator.py radical_500.csv test_500.png
python generator.py radical_5000.csv test_5000.png
```

## 🔧 Explication des étapes techniques principales du programme

### 1. Chargement et normalisation des données
- Lecture du fichier CSV avec pandas
- Extraction des valeurs numériques de chaque ligne
- Normalisation des valeurs entre 0 et 1 pour un contrôle uniforme

### 2. Génération de la palette de couleurs
- Calcul d'une teinte de base à partir du hash SHA-256 du contenu du CSV
- Création d'une palette harmonieuse avec 5 couleurs principales + 2 accents
- Conversion HSL → RGB pour l'affichage

### 3. Création du canevas
- Initialisation d'une image 1080×720 pixels
- Création d'un masque elliptique avec flou gaussien pour cadrer la composition
- Préparation du calque de peinture (transparent)

### 4. Rendu des éléments
Pour chaque ligne du CSV (dans l'ordre z si présent) :
- **Extraction des paramètres** : position (x, y), taille, angle, épaisseur, vigueur, courbures
- **Sélection de la couleur** : basée sur le hash de la ligne
- **Dessin selon le type de forme** :
  - **`blob`** : Polygones concentriques irréguliers avec transparence dégradée
  - **`stroke`** : Courbe de Bézier quadratique avec bruit ajouté pour un effet main levée
  - **`splatter`** : Série d'ellipses le long d'une trajectoire angulaire
  - **`spiral`** : Ligne spiralée avec variations organiques et épaisseur décroissante
  - **`wave`** : Lignes ondulées concentriques avec fréquences variables
  - **`cloud`** : Distribution gaussienne de particules avec transparence dégradée

### 5. Composition finale
- Application du masque elliptique au calque de peinture
- Fusion alpha composite avec le fond clair
- Sauvegarde de l'image finale au format PNG

## 📁 Fichiers annexes

Le dépôt contient plusieurs fichiers de démonstration :

### Fichiers CSV d'exemple
- `radical_10.csv` : Petit échantillon (10 éléments)
- `radical_100.csv` : Échantillon moyen (100 éléments)
- `radical_500.csv` : Grand échantillon (500 éléments)
- `radical_5000.csv` : Très grand échantillon (5000 éléments)

### Autres fichiers
- `requirements.txt` : Dépendances du projet
- `pyproject.toml` : Configuration du projet Python
- `CHANGELOG.md` : Historique des modifications

## 📦 Dépendances

- **Pillow** (>=12.0.0) : Manipulation et génération d'images
- **pandas** (>=2.3.3) : Traitement des fichiers CSV
- **numpy** (>=2.3.4) : Calculs numériques et normalisation

## 💡 Notes techniques

- Les valeurs du CSV sont automatiquement normalisées entre 0 et 1
- Si une ligne contient moins de 12 valeurs numériques, des valeurs aléatoires (mais déterministes) sont générées pour compléter
- La génération est déterministe : le même CSV produira toujours la même image
- Les couleurs sont générées de manière cohérente à partir du contenu global du CSV
- Le masque elliptique avec flou crée un effet de vignettage artistique

## 🎨 Conseils de composition

### Combinaisons de formes efficaces

- **Fond de texture** : Utilisez `cloud` avec de grandes tailles pour créer des fonds atmosphériques
- **Éléments structurels** : `stroke` et `spiral` pour les lignes directrices de la composition
- **Accents dynamiques** : `splatter` pour ajouter de l'énergie et du mouvement
- **Transitions fluides** : `wave` pour connecter visuellement différentes zones
- **Zones de focus** : `blob` pour créer des points d'intérêt doux

## 🎯 Exemple de workflow complet

1. Préparez votre fichier CSV avec les colonnes appropriées
2. Assurez-vous que la colonne `shape` contient uniquement les formes valides : `blob`, `stroke`, `splatter`, `spiral`, `wave`, ou `cloud`
3. Exécutez le générateur : `python generator.py votre_fichier.csv sortie.png`
4. L'image résultante sera sauvegardée dans le fichier spécifié

---

*Projet développé dans le cadre du Hackathon M1 Data & IA*
