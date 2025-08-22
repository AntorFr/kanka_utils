# 🖼️ Guide d'utilisation rapide - Compression intelligente d'images

## 🚀 Utilisation simple

### En une ligne
```python
from kanka_image import smart_compress_folder

# Compresse toutes les images PNG d'un dossier
resultats = smart_compress_folder("/chemin/vers/votre/dossier")
```

### Avec paramètres personnalisés
```python
from kanka_image import smart_compress_folder

# Compression plus agressive
resultats = smart_compress_folder(
    "/chemin/vers/votre/dossier",
    scale_factor=0.3,      # 30% de la taille originale
    palette_size=64,       # 64 couleurs maximum
    overwrite=True         # Remplace les fichiers existants @0.3x
)
```

## 📊 Comprendre les résultats

```python
print(f"Images trouvées: {resultats['total_found']}")
print(f"Images traitées: {len(resultats['processed'])}")
print(f"Images ignorées: {len(resultats['skipped'])}")
print(f"Réduction moyenne: {resultats['overall_reduction']:.1f}%")
```

## 🔧 Utilisation en ligne de commande

```bash
# Mode intelligent (recommandé)
python kanka_image/image_compressor.py /chemin/vers/dossier --smart

# Avec paramètres personnalisés
python kanka_image/image_compressor.py /chemin/vers/dossier --smart -s 0.3 -c 64 -v

# Avec remplacement des fichiers existants
python kanka_image/image_compressor.py /chemin/vers/dossier --smart --overwrite
```

## 📁 Comment ça fonctionne

1. **Détection automatique** : Trouve tous les fichiers PNG dans le dossier
2. **Vérification intelligente** : Vérifie si une version compressée existe déjà
3. **Nommage automatique** : Ajoute `@0.5x` (ou votre facteur) au nom du fichier
4. **Protection** : N'écrase jamais les fichiers existants (sauf si `overwrite=True`)

## 📝 Exemples de noms de fichiers

- `photo.png` → `photo@0.5x.png` (50% de taille)
- `image.png` → `image@0.3x.png` (30% de taille)
- `illustration.png` → `illustration@0.8x.png` (80% de taille)

## ⚡ Avantages

- ✅ **Intelligent** : Ne retraite pas les images déjà compressées
- ✅ **Sûr** : Préserve vos fichiers originaux
- ✅ **Rapide** : Traitement par lots optimisé
- ✅ **Flexible** : Paramètres ajustables pour tous les besoins
- ✅ **Détaillé** : Statistiques complètes de compression

## 🛠️ Paramètres disponibles

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `scale_factor` | 0.5 | Facteur de redimensionnement (0.1 à 1.0) |
| `palette_size` | 256 | Nombre max de couleurs (2 à 256) |
| `overwrite` | False | Remplace les fichiers existants |

---

**💡 Astuce** : Commencez toujours avec les paramètres par défaut, ils donnent d'excellents résultats pour la plupart des cas d'usage !
