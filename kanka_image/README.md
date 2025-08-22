# Module Kanka Image - Compression d'images optimisée

Module de compression d'images PNG spécialement conçu pour optimiser les illustrations des campagnes Kanka.

## 🎯 Fonctionnalités

- **Redimensionnement intelligent** : Réduction à 50% par défaut (configurable)
- **Optimisation palette** : Réduction à 256 couleurs avec algorithmes avancés
- **Compression PNG maximale** : Utilisation des meilleurs paramètres de compression
- **Conservation transparence** : Préservation des canaux alpha
- **Traitement en lot** : Compression multiple de dossiers entiers
- **Interface CLI complète** : Utilisation simple en ligne de commande

## 📦 Installation

Le module utilise **Pillow** qui est déjà installé dans l'environnement Kanka Utils.

```bash
# Pillow est déjà disponible, pas d'installation supplémentaire nécessaire
```

## 🚀 Utilisation rapide

### Compression d'un fichier unique

```bash
# Compression standard (50%, 256 couleurs)
python kanka_image/image_compressor.py portrait.png

# Compression personnalisée
python kanka_image/image_compressor.py portrait.png -s 0.3 -c 128 -o portrait_mini.png
```

### Traitement en lot

```bash
# Compresser toutes les images d'un dossier
python kanka_image/image_compressor.py images/ -b

# Compression agressive pour un dossier
python kanka_image/image_compressor.py images/ -b -s 0.3 -c 64 -o compressed/
```

## 📋 Paramètres disponibles

| Paramètre | Description | Défaut | Exemple |
|-----------|-------------|---------|---------|
| `-s, --scale` | Facteur de redimensionnement (0.1-1.0) | 0.5 | `-s 0.3` |
| `-c, --colors` | Nombre maximum de couleurs (2-256) | 256 | `-c 128` |
| `-o, --output` | Fichier/dossier de sortie | Auto | `-o compressed.png` |
| `-b, --batch` | Mode traitement en lot | False | `-b` |
| `-v, --verbose` | Affichage détaillé | False | `-v` |
| `--no-palette` | Désactiver réduction palette | False | `--no-palette` |

## 🧪 Tests

Testez le module avec l'outil de test intégré :

```bash
python kanka_image/test_compress.py
```

Ce test génère une image colorée et teste différents niveaux de compression.

## 📊 Résultats typiques

Pour une image typique de 800x600 pixels :

| Compression | Taille finale | Réduction | Usage recommandé |
|-------------|---------------|-----------|------------------|
| Standard (50%, 256c) | ~33% plus petite | ~30-35% | Portraits, illustrations générales |
| Agressive (30%, 64c) | ~80% plus petite | ~75-80% | Icônes, images simples |
| Légère (80%, 256c) | Variable | 0-20% | Images détaillées importantes |

## 🛠️ Utilisation programmatique

```python
from kanka_image.compress import compress_png, batch_compress_images

# Compresser un fichier
success = compress_png(
    "image.png", 
    "compressed.png", 
    scale_factor=0.5, 
    palette_size=256
)

# Compresser un dossier
files = batch_compress_images(
    "images/", 
    "compressed/", 
    scale_factor=0.3, 
    palette_size=128
)
```

## 🎨 Optimisations appliquées

1. **Redimensionnement LANCZOS** : Algorithme de haute qualité pour le redimensionnement
2. **Quantification MEDIANCUT** : Réduction optimale de la palette de couleurs
3. **Compression PNG niveau 9** : Compression maximale sans perte
4. **Préservation alpha** : Conservation de la transparence avec gestion séparée
5. **Optimisation automatique** : Paramètres PNG optimisés selon le contenu

## 📁 Structure du module

```
kanka_image/
├── __init__.py           # Points d'entrée du module
├── compress.py           # Moteur de compression principal
├── config.py             # Configuration et constantes
├── image_compressor.py   # Script CLI principal
├── test_compress.py      # Tests automatisés
└── README.md            # Cette documentation
```

## 🔧 Intégration avec Kanka Utils

Le module peut être intégré dans l'interface Streamlit pour permettre l'upload et la compression automatique d'images directement depuis l'interface web.

## 💡 Conseils d'utilisation

- **Portraits de personnages** : Utilisez `-s 0.5 -c 256` (standard)
- **Icônes et symboles** : Utilisez `-s 0.3 -c 64` (agressive)
- **Cartes détaillées** : Utilisez `-s 0.7 -c 256` (légère)
- **Backgrounds** : Utilisez `-s 0.4 -c 128` (équilibrée)

## ⚠️ Notes importantes

- Seuls les fichiers PNG sont supportés actuellement
- La transparence est préservée mais peut être affectée par la réduction de palette
- Les images déjà optimisées peuvent parfois augmenter de taille avec une compression légère
- Testez toujours sur un échantillon avant un traitement en lot important
