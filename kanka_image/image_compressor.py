#!/usr/bin/env python3
"""
Script principal de compression d'images pour Kanka
==================================================

Utilisation :
    python image_compressor.py image.png                    # Compresser une image
    python image_compressor.py images/ -b                   # Compresser un dossier
    python image_compressor.py image.png -s 0.3 -c 128     # Personnaliser les paramètres
    python image_compressor.py images/ --tokens             # Créer des tokens circulaires

Exemples :
    # Compresser une image à 50% avec 256 couleurs
    python image_compressor.py portrait.png
    
    # Compresser toutes les images d'un dossier à 30% avec 128 couleurs
    python image_compressor.py images/ -b -s 0.3 -c 128
    
    # Compresser avec sortie personnalisée
    python image_compressor.py image.png -o compressed_image.png
    
    # Créer des tokens circulaires à partir des images @0.5x 
    python image_compressor.py images/ --tokens --token-scale 0.5
    
    # Créer des tokens plus petits à partir des images originales
    python image_compressor.py images/ --tokens --token-source original --token-scale 0.3
"""

import os
import sys
import argparse
from pathlib import Path

# Ajouter le répertoire parent au path pour importer kanka_image
sys.path.insert(0, str(Path(__file__).parent.parent))

from kanka_image.compress import ImageCompressor, compress_folder_smart, smart_create_tokens
from kanka_image.config import DEFAULT_SCALE_FACTOR, DEFAULT_PALETTE_SIZE

def main():
    parser = argparse.ArgumentParser(
        description="Compresseur d'images PNG optimisé pour Kanka",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation :
  %(prog)s image.png                        # Compression standard (50%%, 256 couleurs)
  %(prog)s images/ -b                       # Traitement en lot d'un dossier
  %(prog)s image.png -s 0.3 -c 128         # 30%% de taille, 128 couleurs
  %(prog)s image.png -o small_image.png     # Sortie personnalisée
        """
    )
    
    # Arguments principaux
    parser.add_argument(
        "input",
        help="Fichier PNG ou dossier à traiter"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Fichier ou dossier de sortie (optionnel)"
    )
    
    # Options de compression
    parser.add_argument(
        "-s", "--scale",
        type=float,
        default=DEFAULT_SCALE_FACTOR,
        help=f"Facteur de redimensionnement (défaut: {DEFAULT_SCALE_FACTOR})"
    )
    
    parser.add_argument(
        "-c", "--colors",
        type=int,
        default=DEFAULT_PALETTE_SIZE,
        help=f"Nombre maximum de couleurs (défaut: {DEFAULT_PALETTE_SIZE})"
    )
    
    # Options de traitement
    parser.add_argument(
        "-b", "--batch",
        action="store_true",
        help="Mode batch pour traiter tous les PNG d'un dossier"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Affichage détaillé"
    )
    
    parser.add_argument(
        "--no-palette",
        action="store_true",
        help="Désactiver la réduction de palette"
    )
    
    parser.add_argument(
        "--smart",
        action="store_true",
        help="Mode intelligent : crée des versions @{scale}x seulement si elles n'existent pas"
    )
    
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Écrase les fichiers compressés existants (utilisé avec --smart)"
    )
    
    parser.add_argument(
        "--tokens",
        action="store_true",
        help="Créer des tokens circulaires à partir des images compressées"
    )
    
    parser.add_argument(
        "--token-scale",
        type=float,
        default=0.5,
        help="Facteur de redimensionnement pour les tokens (défaut: 0.5)"
    )
    
    parser.add_argument(
        "--token-source",
        default="@0.5x",
        help="Suffixe des images sources pour créer les tokens (défaut: @0.5x)"
    )

    args = parser.parse_args()
    
    # Validation des arguments
    if not os.path.exists(args.input):
        print(f"❌ Erreur : Le fichier ou dossier '{args.input}' n'existe pas")
        return 1
    
    if args.scale <= 0 or args.scale > 1:
        print(f"❌ Erreur : Le facteur d'échelle doit être entre 0 et 1 (actuel: {args.scale})")
        return 1
    
    if args.colors < 2 or args.colors > 256:
        print(f"❌ Erreur : Le nombre de couleurs doit être entre 2 et 256 (actuel: {args.colors})")
        return 1
    
    # Configuration du compresseur
    compressor = ImageCompressor(palette_size=args.colors)
    
    # Déterminer le mode de traitement
    is_directory = os.path.isdir(args.input)
    batch_mode = args.batch or is_directory
    smart_mode = args.smart or (is_directory and not args.batch)
    
    if smart_mode and is_directory:
        # Mode intelligent pour dossier
        print(f"🧠 Mode intelligent activé pour : {args.input}")
        print(f"📐 Paramètres : {int(args.scale*100)}% de taille, {args.colors} couleurs max")
        if args.overwrite:
            print("⚠️  Mode écrasement activé")
        
        result = compress_folder_smart(
            args.input,
            scale_factor=args.scale,
            palette_size=args.colors,
            overwrite=args.overwrite
        )
        
        if result['success']:
            print(f"✅ Traitement intelligent terminé")
            print(f"📊 Statistiques :")
            print(f"  📁 Fichiers PNG trouvés : {result['total_found']}")
            print(f"  🖼️  Fichiers originaux : {result['original_files']}")
            print(f"  ✅ Fichiers traités : {len(result['processed'])}")
            print(f"  ⏭️  Fichiers ignorés : {len(result['skipped'])}")
            print(f"  ❌ Erreurs : {len(result['errors'])}")
            
            if result['processed']:
                print(f"  📉 Réduction globale : {result['overall_reduction']:.1f}%")
                print(f"  💾 Taille avant : {result['total_size_before']/1024:.1f} KB")
                print(f"  💾 Taille après : {result['total_size_after']/1024:.1f} KB")
            
            if args.verbose:
                if result['processed']:
                    print("\n📋 Fichiers traités :")
                    for item in result['processed']:
                        fname = Path(item['original']).name
                        cfname = Path(item['compressed']).name
                        print(f"  ✅ {fname} -> {cfname} ({item['reduction_percent']:.1f}% réduction)")
                
                if result['skipped']:
                    print("\n⏭️  Fichiers ignorés :")
                    for item in result['skipped']:
                        fname = Path(item['original']).name
                        cfname = Path(item['compressed']).name
                        print(f"  ⏭️  {fname} -> {cfname} (déjà existant)")
                
                if result['errors']:
                    print("\n❌ Erreurs :")
                    for item in result['errors']:
                        fname = Path(item['file']).name
                        print(f"  ❌ {fname}: {item['error']}")
        else:
            print(f"❌ Erreur : {result.get('error', 'Erreur inconnue')}")
            return 1
            
    elif batch_mode:
        # Mode batch
        print(f"🔄 Traitement en lot du dossier : {args.input}")
        print(f"📐 Paramètres : {int(args.scale*100)}% de taille, {args.colors} couleurs max")
        
        result = compressor.batch_compress_images(
            args.input,
            args.output,
            args.scale
        )
        
        if result:
            print(f"✅ Traitement terminé : {len(result)} fichiers compressés")
            if args.verbose:
                for file in result:
                    print(f"  📁 {Path(file).name}")
        else:
            print("❌ Aucun fichier traité avec succès")
            return 1
            
    else:
        # Fichier unique
        if not args.input.lower().endswith(('.png', '.PNG')):
            print(f"❌ Erreur : Seuls les fichiers PNG sont supportés")
            return 1
        
        print(f"🖼️  Compression de : {args.input}")
        print(f"📐 Paramètres : {int(args.scale*100)}% de taille, {args.colors} couleurs max")
        
        success = compressor.compress_png(
            args.input,
            args.output,
            args.scale,
            force_palette=not args.no_palette
        )
        
        if success:
            output_file = args.output or str(Path(args.input).with_stem(Path(args.input).stem + "_compressed"))
            print(f"✅ Compression réussie : {output_file}")
        else:
            print("❌ Échec de la compression")
            return 1
    
    # Traitement des tokens circulaires si demandé
    if args.tokens:
        if not is_directory:
            print("⚠️  La création de tokens ne fonctionne qu'avec des dossiers")
            return 1
        
        print(f"\n🎯 Création de tokens circulaires...")
        print(f"📐 Paramètres tokens : {int(args.token_scale*100)}% de taille, source '{args.token_source}'")
        
        token_result = smart_create_tokens(
            args.input,
            scale_factor=args.token_scale,
            source_suffix=args.token_source if args.token_source != "original" else ""
        )
        
        if "error" not in token_result:
            print(f"✅ Création de tokens terminée")
            print(f"📊 Statistiques tokens :")
            print(f"  🎯 Tokens créés : {len(token_result['processed'])}")
            print(f"  ⏭️  Tokens ignorés : {len(token_result['skipped'])}")
            print(f"  ❌ Erreurs : {len(token_result['errors'])}")
            
            if args.verbose:
                if token_result['processed']:
                    print("\n📋 Tokens créés :")
                    for token_path in token_result['processed']:
                        token_name = Path(token_path).name
                        print(f"  🎯 {token_name}")
                
                if token_result['skipped']:
                    print("\n⏭️  Tokens ignorés :")
                    for token_path in token_result['skipped']:
                        token_name = Path(token_path).name
                        print(f"  ⏭️  {token_name} (déjà existant)")
                
                if token_result['errors']:
                    print("\n❌ Erreurs tokens :")
                    for error in token_result['errors']:
                        print(f"  ❌ {error}")
        else:
            print(f"❌ Erreur lors de la création des tokens : {token_result['error']}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
