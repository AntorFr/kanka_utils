"""
Utilitaires pour intégration Streamlit du module kanka_image
===========================================================

Fonctions helper pour l'interface web de compression d'images
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
from typing import List, Optional
from PIL import Image
import io

from .compress import compress_png, batch_compress_images

def streamlit_image_uploader(key: str = "image_upload") -> Optional[List[bytes]]:
    """
    Widget Streamlit pour upload d'images PNG
    
    Args:
        key: Clé unique pour le widget
        
    Returns:
        Liste des contenus d'images uploadées ou None
    """
    uploaded_files = st.file_uploader(
        "Choisissez des images PNG à compresser",
        type=['png'],
        accept_multiple_files=True,
        key=key,
        help="Sélectionnez une ou plusieurs images PNG à optimiser"
    )
    
    if uploaded_files:
        return [file.getvalue() for file in uploaded_files]
    return None

def streamlit_compression_settings() -> dict:
    """
    Interface Streamlit pour les paramètres de compression
    
    Returns:
        Dictionnaire avec les paramètres de compression
    """
    st.markdown("### ⚙️ Paramètres de compression")
    
    col1, col2 = st.columns(2)
    
    with col1:
        scale_factor = st.slider(
            "📐 Facteur de redimensionnement",
            min_value=0.1,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="Proportion de la taille originale (0.5 = 50%)"
        )
        
    with col2:
        palette_size = st.selectbox(
            "🎨 Nombre de couleurs",
            options=[256, 128, 64, 32, 16],
            index=0,
            help="Nombre maximum de couleurs dans l'image finale"
        )
    
    # Options avancées
    with st.expander("🔧 Options avancées"):
        force_palette = st.checkbox(
            "Forcer la réduction de palette",
            value=True,
            help="Applique la réduction de couleurs même si l'image en a moins"
        )
        
        preserve_quality = st.checkbox(
            "Mode qualité maximale",
            value=False,
            help="Privilégie la qualité sur la taille du fichier"
        )
    
    return {
        'scale_factor': scale_factor,
        'palette_size': palette_size,
        'force_palette': force_palette,
        'preserve_quality': preserve_quality
    }

def streamlit_compress_images(image_data: List[bytes], 
                             filenames: List[str],
                             settings: dict) -> List[tuple]:
    """
    Compresse les images uploadées avec interface Streamlit
    
    Args:
        image_data: Liste des contenus d'images
        filenames: Liste des noms de fichiers
        settings: Paramètres de compression
        
    Returns:
        Liste de tuples (nom_fichier, données_compressées, stats)
    """
    results = []
    
    # Barre de progression
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (data, filename) in enumerate(zip(image_data, filenames)):
        status_text.text(f"Compression de {filename}...")
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_input:
            # Sauvegarder l'image uploadée
            temp_input.write(data)
            temp_input.flush()
            
            # Fichier de sortie temporaire
            with tempfile.NamedTemporaryFile(suffix='_compressed.png', delete=False) as temp_output:
                temp_output_path = temp_output.name
            
            try:
                # Compression
                success = compress_png(
                    temp_input.name,
                    temp_output_path,
                    scale_factor=settings['scale_factor'],
                    palette_size=settings['palette_size']
                )
                
                if success and os.path.exists(temp_output_path):
                    # Lire le résultat
                    with open(temp_output_path, 'rb') as f:
                        compressed_data = f.read()
                    
                    # Statistiques
                    original_size = len(data)
                    compressed_size = len(compressed_data)
                    reduction = (1 - compressed_size / original_size) * 100
                    
                    # Dimensions de l'image
                    original_img = Image.open(io.BytesIO(data))
                    compressed_img = Image.open(io.BytesIO(compressed_data))
                    
                    stats = {
                        'original_size': original_size,
                        'compressed_size': compressed_size,
                        'reduction_percent': reduction,
                        'original_dimensions': original_img.size,
                        'compressed_dimensions': compressed_img.size
                    }
                    
                    results.append((filename, compressed_data, stats))
                else:
                    st.error(f"❌ Échec de la compression de {filename}")
                    
            finally:
                # Nettoyer les fichiers temporaires
                try:
                    os.unlink(temp_input.name)
                    os.unlink(temp_output_path)
                except:
                    pass
        
        # Mettre à jour la progression
        progress_bar.progress((i + 1) / len(image_data))
    
    # Finaliser
    progress_bar.empty()
    status_text.empty()
    
    return results

def streamlit_display_results(results: List[tuple]):
    """
    Affiche les résultats de compression dans Streamlit
    
    Args:
        results: Liste de tuples (nom_fichier, données_compressées, stats)
    """
    if not results:
        st.warning("Aucune image compressée avec succès.")
        return
    
    st.markdown("### 📊 Résultats de la compression")
    
    # Statistiques globales
    total_original = sum(stats['original_size'] for _, _, stats in results)
    total_compressed = sum(stats['compressed_size'] for _, _, stats in results)
    overall_reduction = (1 - total_compressed / total_original) * 100 if total_original > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Images traitées", len(results))
    with col2:
        st.metric("Taille originale totale", f"{total_original / 1024:.1f} KB")
    with col3:
        st.metric("Réduction globale", f"{overall_reduction:.1f}%")
    
    # Détails par image
    st.markdown("#### 📋 Détails par image")
    
    for filename, compressed_data, stats in results:
        with st.expander(f"📸 {filename}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Avant compression:**")
                st.write(f"• Taille: {stats['original_size'] / 1024:.1f} KB")
                st.write(f"• Dimensions: {stats['original_dimensions'][0]}×{stats['original_dimensions'][1]}")
                
            with col2:
                st.markdown("**Après compression:**")
                st.write(f"• Taille: {stats['compressed_size'] / 1024:.1f} KB")
                st.write(f"• Dimensions: {stats['compressed_dimensions'][0]}×{stats['compressed_dimensions'][1]}")
                st.write(f"• Réduction: {stats['reduction_percent']:.1f}%")
            
            # Bouton de téléchargement
            st.download_button(
                label=f"⬇️ Télécharger {filename}",
                data=compressed_data,
                file_name=f"compressed_{filename}",
                mime="image/png",
                key=f"download_{filename}"
            )

def streamlit_image_compression_page():
    """
    Page complète Streamlit pour la compression d'images
    Peut être appelée depuis l'interface principale
    """
    st.title("🖼️ Compression d'images pour Kanka")
    st.markdown("Optimisez vos images PNG pour réduire leur taille tout en conservant la qualité.")
    
    # Upload des images
    image_files = st.file_uploader(
        "Choisissez des images PNG à compresser",
        type=['png'],
        accept_multiple_files=True,
        help="Sélectionnez une ou plusieurs images PNG à optimiser"
    )
    
    if image_files:
        # Paramètres de compression
        settings = streamlit_compression_settings()
        
        # Bouton de compression
        if st.button("🚀 Compresser les images", type="primary"):
            with st.spinner("Compression en cours..."):
                # Extraire les données et noms
                image_data = [file.getvalue() for file in image_files]
                filenames = [file.name for file in image_files]
                
                # Compresser
                results = streamlit_compress_images(image_data, filenames, settings)
                
                # Afficher les résultats
                streamlit_display_results(results)
                
                if results:
                    st.success(f"✅ {len(results)} image(s) compressée(s) avec succès !")
    else:
        st.info("👆 Uploadez des images PNG pour commencer la compression.")
        
        # Aide et exemples
        with st.expander("💡 Aide et conseils"):
            st.markdown("""
            **Conseils d'utilisation:**
            
            - **Portraits de personnages**: 50% de taille, 256 couleurs
            - **Icônes et symboles**: 30% de taille, 64 couleurs  
            - **Cartes détaillées**: 70% de taille, 256 couleurs
            - **Images de fond**: 40% de taille, 128 couleurs
            
            **Formats supportés:**
            - PNG avec ou sans transparence
            - Toutes résolutions
            - Images couleur et niveaux de gris
            """)

def format_file_size(size_bytes: int) -> str:
    """Formate une taille de fichier en format lisible."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_common_image_folders() -> List[tuple]:
    """Retourne les dossiers d'images communs sur macOS."""
    home = Path.home()
    folders = [
        ("🏠 Dossier utilisateur", str(home)),
        ("🖼️ Images", str(home / "Pictures")),
        ("🖥️ Bureau", str(home / "Desktop")),
        ("📁 Documents", str(home / "Documents")),
        ("📥 Téléchargements", str(home / "Downloads")),
    ]
    
    # Filtrer seulement les dossiers qui existent
    return [(name, path) for name, path in folders if Path(path).exists()]


def validate_folder_path(folder_path: str) -> tuple[bool, str, List[Path]]:
    """
    Valide un chemin de dossier et retourne les informations.
    
    Returns:
        tuple: (is_valid, message, png_files_list)
    """
    if not folder_path:
        return False, "Veuillez entrer un chemin de dossier", []
    
    folder_path_obj = Path(folder_path)
    
    if not folder_path_obj.exists():
        return False, "❌ Ce dossier n'existe pas", []
    
    if not folder_path_obj.is_dir():
        return False, "❌ Ce chemin n'est pas un dossier", []
    
    # Compter les fichiers PNG
    try:
        png_files = list(folder_path_obj.glob("*.png"))
        if len(png_files) == 0:
            return True, "⚠️ Aucun fichier PNG trouvé dans ce dossier", []
        else:
            return True, f"✅ Dossier valide : {len(png_files)} fichiers PNG trouvés", png_files
    except PermissionError:
        return False, "❌ Accès refusé à ce dossier", []


def display_compression_results(resultats: dict):
    """Affiche les résultats de compression de manière formatée."""
    if not resultats.get('success', False):
        st.error("❌ Erreur durant la compression")
        return
    
    # Message de succès
    st.success("🎉 Compression terminée avec succès !")
    
    # Métriques principales
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        st.metric("Images trouvées", resultats['total_found'])
    
    with col_m2:
        st.metric("Images traitées", len(resultats['processed']))
    
    with col_m3:
        st.metric("Images ignorées", len(resultats['skipped']))
    
    with col_m4:
        if resultats['processed']:
            st.metric("Réduction moyenne", f"{resultats['overall_reduction']:.1f}%")
        else:
            st.metric("Réduction", "0%")
    
    # Détails des images traitées
    if resultats['processed']:
        st.markdown("### ✅ Images compressées")
        for item in resultats['processed']:
            original_size = format_file_size(item['original_size'])
            compressed_size = format_file_size(item['compressed_size'])
            reduction = item['reduction_percent']
            
            col_name, col_sizes = st.columns([2, 1])
            with col_name:
                st.text(f"📸 {Path(item['original']).name}")
                st.text(f"   → {Path(item['compressed']).name}")
            with col_sizes:
                st.text(f"{original_size} → {compressed_size}")
                st.text(f"💾 -{reduction:.1f}%")
    
    # Images ignorées
    if resultats['skipped']:
        with st.expander(f"📝 Images ignorées ({len(resultats['skipped'])})"):
            for item in resultats['skipped']:
                reason = item.get('reason', 'unknown')
                if reason == 'already_exists':
                    st.text(f"📸 {Path(item['original']).name} (déjà compressé)")
                else:
                    st.text(f"📸 {Path(item['original']).name} ({reason})")
    
    # Erreurs
    if resultats['errors']:
        st.markdown("### ❌ Erreurs")
        for error in resultats['errors']:
            st.error(f"• {error}")


if __name__ == "__main__":
    # Test standalone de la page
    streamlit_image_compression_page()
