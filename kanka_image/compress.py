"""
Module de compression d'images pour Kanka
========================================

Ce module fournit des outils pour compresser efficacement les images PNG
utilisées dans les campagnes Kanka, en appliquant :
- Redimensionnement à 50% de la taille originale
- Réduction de la palette à 256 couleurs
- Compression avancée avec optimisation

Dépendances :
- Pillow (PIL) : manipulation d'images
- pngquant-python : compression PNG avancée (optionnel)
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image, ImageOps
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageCompressor:
    """Classe pour la compression d'images PNG avec optimisations avancées"""
    
    def __init__(self, quality: int = 85, palette_size: int = 256):
        """
        Initialise le compresseur d'images
        
        Args:
            quality: Qualité de compression (0-100)
            palette_size: Nombre de couleurs dans la palette (max 256)
        """
        self.quality = quality
        self.palette_size = min(palette_size, 256)
        
    def compress_png(self, 
                    input_path: str, 
                    output_path: Optional[str] = None,
                    scale_factor: float = 0.5,
                    force_palette: bool = True) -> bool:
        """
        Compresse une image PNG avec les optimisations suivantes :
        - Redimensionnement selon scale_factor
        - Réduction de palette à palette_size couleurs
        - Compression optimisée
        
        Args:
            input_path: Chemin vers l'image source
            output_path: Chemin de sortie (optionnel, par défaut ajoute '_compressed')
            scale_factor: Facteur de redimensionnement (0.5 = 50%)
            force_palette: Force la conversion en palette de couleurs
            
        Returns:
            bool: True si la compression a réussi
        """
        try:
            # Vérifier que le fichier existe
            if not os.path.exists(input_path):
                logger.error(f"Fichier non trouvé : {input_path}")
                return False
            
            # Générer le chemin de sortie si non spécifié
            if output_path is None:
                path = Path(input_path)
                output_path = str(path.parent / f"{path.stem}_compressed{path.suffix}")
            
            # Ouvrir l'image
            logger.info(f"Ouverture de l'image : {input_path}")
            with Image.open(input_path) as img:
                # Informations de l'image originale
                original_size = img.size
                original_mode = img.mode
                original_file_size = os.path.getsize(input_path)
                
                logger.info(f"Image originale : {original_size[0]}x{original_size[1]}, "
                           f"mode: {original_mode}, taille: {original_file_size/1024:.1f} KB")
                
                # Convertir en RGBA si nécessaire pour préserver la transparence
                if img.mode not in ('RGBA', 'RGB'):
                    img = img.convert('RGBA')
                
                # Redimensionnement
                new_size = (int(original_size[0] * scale_factor), 
                           int(original_size[1] * scale_factor))
                
                logger.info(f"Redimensionnement vers : {new_size[0]}x{new_size[1]}")
                img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Réduction de palette si demandée
                if force_palette and self.palette_size < 256:
                    logger.info(f"Réduction de la palette à {self.palette_size} couleurs")
                    
                    # Séparer l'alpha channel si présent
                    if img_resized.mode == 'RGBA':
                        # Créer une image RGB sur fond blanc pour la quantification
                        rgb_img = Image.new('RGB', img_resized.size, (255, 255, 255))
                        rgb_img.paste(img_resized, mask=img_resized.split()[-1])
                        
                        # Quantifier l'image RGB
                        quantized = rgb_img.quantize(colors=self.palette_size, method=Image.Quantize.MEDIANCUT)
                        
                        # Reconvertir en RGBA en appliquant l'alpha original
                        final_img = quantized.convert('RGBA')
                        alpha = img_resized.split()[-1]
                        final_img.putalpha(alpha)
                    else:
                        # Quantification directe pour les images sans alpha
                        final_img = img_resized.quantize(colors=self.palette_size, method=Image.Quantize.MEDIANCUT)
                        final_img = final_img.convert('RGB')
                else:
                    final_img = img_resized
                
                # Sauvegarde avec compression optimisée
                logger.info(f"Sauvegarde vers : {output_path}")
                
                # Options de sauvegarde PNG optimisées
                save_kwargs = {
                    'format': 'PNG',
                    'optimize': True,
                }
                
                # Ajuster selon le mode final
                if final_img.mode == 'P':  # Image avec palette
                    save_kwargs['bits'] = 8
                elif final_img.mode == 'RGBA':
                    save_kwargs['compress_level'] = 9  # Compression maximale
                
                final_img.save(output_path, **save_kwargs)
                
                # Statistiques finales
                final_file_size = os.path.getsize(output_path)
                compression_ratio = (1 - final_file_size / original_file_size) * 100
                
                logger.info(f"Compression terminée !")
                logger.info(f"Taille originale : {original_file_size/1024:.1f} KB")
                logger.info(f"Taille finale : {final_file_size/1024:.1f} KB")
                logger.info(f"Compression : {compression_ratio:.1f}%")
                
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de la compression : {str(e)}")
            return False
    
    def batch_compress_images(self, 
                             input_dir: str, 
                             output_dir: Optional[str] = None,
                             scale_factor: float = 0.5,
                             pattern: str = "*.png") -> List[str]:
        """
        Compresse toutes les images PNG d'un dossier
        
        Args:
            input_dir: Dossier source
            output_dir: Dossier de destination (optionnel)
            scale_factor: Facteur de redimensionnement
            pattern: Pattern de fichiers à traiter
            
        Returns:
            List[str]: Liste des fichiers traités avec succès
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            logger.error(f"Dossier source non trouvé : {input_dir}")
            return []
        
        # Dossier de sortie
        if output_dir is None:
            output_path = input_path / "compressed"
        else:
            output_path = Path(output_dir)
        
        # Créer le dossier de sortie
        output_path.mkdir(exist_ok=True)
        
        # Trouver tous les fichiers PNG
        png_files = list(input_path.glob(pattern))
        logger.info(f"Trouvé {len(png_files)} fichiers à traiter")
        
        successful_files = []
        
        for png_file in png_files:
            output_file = output_path / png_file.name
            logger.info(f"Traitement : {png_file.name}")
            
            if self.compress_png(str(png_file), str(output_file), scale_factor):
                successful_files.append(str(png_file))
            else:
                logger.warning(f"Échec du traitement : {png_file.name}")
        
        logger.info(f"Traitement terminé : {len(successful_files)}/{len(png_files)} fichiers réussis")
        return successful_files

def compress_folder_smart(folder_path: str, 
                          scale_factor: float = 0.5,
                          palette_size: int = 256,
                          overwrite: bool = False) -> dict:
    """
    Compresse intelligemment toutes les images PNG d'un dossier.
    Crée des versions compressées avec le suffixe @{scale}x uniquement si elles n'existent pas.
    
    Args:
        folder_path: Chemin vers le dossier contenant les images
        scale_factor: Facteur de redimensionnement (0.5 = 50%)
        palette_size: Nombre maximum de couleurs (256 par défaut)
        overwrite: Si True, écrase les fichiers existants
        
    Returns:
        dict: Statistiques du traitement avec listes des fichiers traités/ignorés
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        logger.error(f"Dossier non trouvé : {folder_path}")
        return {
            'success': False,
            'error': f"Dossier non trouvé : {folder_path}",
            'processed': [],
            'skipped': [],
            'errors': []
        }
    
    if not folder.is_dir():
        logger.error(f"Le chemin n'est pas un dossier : {folder_path}")
        return {
            'success': False,
            'error': f"Le chemin n'est pas un dossier : {folder_path}",
            'processed': [],
            'skipped': [],
            'errors': []
        }
    
    # Trouver tous les fichiers PNG
    png_files = list(folder.glob("*.png")) + list(folder.glob("*.PNG"))
    logger.info(f"Trouvé {len(png_files)} fichiers PNG dans {folder_path}")
    
    # Filtrer les fichiers déjà compressés (contenant @)
    original_files = [f for f in png_files if '@' not in f.stem]
    logger.info(f"Fichiers originaux à traiter : {len(original_files)}")
    
    # Générer le suffixe pour les fichiers compressés
    if scale_factor == 0.5:
        suffix = "@0.5x"
    else:
        # Formatage propre du facteur d'échelle
        if scale_factor == int(scale_factor):
            suffix = f"@{int(scale_factor)}x"
        else:
            suffix = f"@{scale_factor}x"
    
    # Initialiser les statistiques
    stats = {
        'success': True,
        'total_found': len(png_files),
        'original_files': len(original_files),
        'processed': [],
        'skipped': [],
        'errors': [],
        'total_size_before': 0,
        'total_size_after': 0
    }
    
    compressor = ImageCompressor(palette_size=palette_size)
    
    for png_file in original_files:
        # Générer le nom du fichier compressé
        compressed_name = f"{png_file.stem}{suffix}{png_file.suffix}"
        compressed_path = png_file.parent / compressed_name
        
        # Vérifier si le fichier compressé existe déjà
        if compressed_path.exists() and not overwrite:
            logger.info(f"Fichier compressé existe déjà, ignoré : {compressed_name}")
            stats['skipped'].append({
                'original': str(png_file),
                'compressed': str(compressed_path),
                'reason': 'already_exists'
            })
            continue
        
        # Obtenir la taille du fichier original
        try:
            original_size = png_file.stat().st_size
            stats['total_size_before'] += original_size
        except Exception as e:
            logger.error(f"Impossible de lire la taille de {png_file.name} : {e}")
            stats['errors'].append({
                'file': str(png_file),
                'error': f"Lecture taille impossible : {e}"
            })
            continue
        
        # Compression
        logger.info(f"Compression de : {png_file.name} -> {compressed_name}")
        
        try:
            success = compressor.compress_png(
                str(png_file),
                str(compressed_path),
                scale_factor=scale_factor,
                force_palette=True
            )
            
            if success and compressed_path.exists():
                # Calculer les statistiques
                compressed_size = compressed_path.stat().st_size
                stats['total_size_after'] += compressed_size
                reduction = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                
                stats['processed'].append({
                    'original': str(png_file),
                    'compressed': str(compressed_path),
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'reduction_percent': reduction
                })
                
                logger.info(f"✅ {png_file.name} -> {compressed_name} "
                           f"({original_size/1024:.1f}KB -> {compressed_size/1024:.1f}KB, "
                           f"{reduction:.1f}% réduction)")
            else:
                stats['errors'].append({
                    'file': str(png_file),
                    'error': "Compression échouée"
                })
                logger.error(f"❌ Échec compression : {png_file.name}")
                
        except Exception as e:
            stats['errors'].append({
                'file': str(png_file),
                'error': str(e)
            })
            logger.error(f"❌ Erreur lors de la compression de {png_file.name} : {e}")
    
    # Calculer les statistiques finales
    if stats['total_size_before'] > 0:
        overall_reduction = (1 - stats['total_size_after'] / stats['total_size_before']) * 100
    else:
        overall_reduction = 0
    
    stats['overall_reduction'] = overall_reduction
    
    # Log final
    logger.info(f"Traitement terminé pour {folder_path}")
    logger.info(f"Traités: {len(stats['processed'])}, Ignorés: {len(stats['skipped'])}, "
               f"Erreurs: {len(stats['errors'])}")
    if stats['processed']:
        logger.info(f"Réduction globale: {overall_reduction:.1f}% "
                   f"({stats['total_size_before']/1024:.1f}KB -> {stats['total_size_after']/1024:.1f}KB)")
    
    return stats

# Fonctions de convenance
def smart_compress_folder(folder_path: str, 
                          scale_factor: float = 0.5,
                          palette_size: int = 256,
                          overwrite: bool = False) -> dict:
    """
    Fonction de convenance pour la compression intelligente d'un dossier.
    Wrapper simplifié autour de compress_folder_smart.
    
    Args:
        folder_path: Chemin vers le dossier contenant les images
        scale_factor: Facteur de redimensionnement (0.5 = 50%)
        palette_size: Nombre maximum de couleurs (256 par défaut)
        overwrite: Si True, écrase les fichiers existants
        
    Returns:
        dict: Résultats du traitement
    """
    return compress_folder_smart(folder_path, scale_factor, palette_size, overwrite)


def compress_png(input_path: str,
                 output_path: Optional[str] = None,
                 scale_factor: float = 0.5,
                 palette_size: int = 256) -> bool:
    """
    Fonction de convenance pour compresser une image PNG
    
    Args:
        input_path: Chemin vers l'image source
        output_path: Chemin de sortie (optionnel)
        scale_factor: Facteur de redimensionnement (0.5 = 50%)
        palette_size: Nombre de couleurs max (256 par défaut)
        
    Returns:
        bool: True si succès
    """
    compressor = ImageCompressor(palette_size=palette_size)
    return compressor.compress_png(input_path, output_path, scale_factor)

def batch_compress_images(input_dir: str, 
                         output_dir: Optional[str] = None,
                         scale_factor: float = 0.5,
                         palette_size: int = 256) -> List[str]:
    """
    Fonction de convenance pour compresser un lot d'images
    
    Args:
        input_dir: Dossier source
        output_dir: Dossier de destination (optionnel)
        scale_factor: Facteur de redimensionnement
        palette_size: Nombre de couleurs max
        
    Returns:
        List[str]: Fichiers traités avec succès
    """
    compressor = ImageCompressor(palette_size=palette_size)
    return compressor.batch_compress_images(input_dir, output_dir, scale_factor)

if __name__ == "__main__":
    # Interface en ligne de commande simple
    import argparse
    
    parser = argparse.ArgumentParser(description="Compresseur d'images PNG pour Kanka")
    parser.add_argument("input", help="Fichier ou dossier d'entrée")
    parser.add_argument("-o", "--output", help="Fichier ou dossier de sortie")
    parser.add_argument("-s", "--scale", type=float, default=0.5, 
                       help="Facteur de redimensionnement (défaut: 0.5)")
    parser.add_argument("-c", "--colors", type=int, default=256,
                       help="Nombre de couleurs max (défaut: 256)")
    parser.add_argument("-b", "--batch", action="store_true",
                       help="Mode batch pour traiter un dossier")
    
    args = parser.parse_args()
    
    if args.batch or os.path.isdir(args.input):
        # Mode batch
        result = batch_compress_images(args.input, args.output, args.scale, args.colors)
        print(f"Traitement terminé : {len(result)} fichiers compressés")
    else:
        # Fichier unique
        success = compress_png(args.input, args.output, args.scale, args.colors)
        if success:
            print("Compression réussie !")
        else:
            print("Échec de la compression")
            sys.exit(1)
