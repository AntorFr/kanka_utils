import streamlit as st
import os
import json
import traceback
from typing import Optional, List
from pathlib import Path

# Import des fonctions du main
from main import (
    update_knowledge_base, generate_system, generate_structure, 
    export_system_from_kanka, export_all_systems, export_all_systems_with_progress, import_system,
    import_location, import_characters, enrich_system, enrich_structure,
    generate_system_synthesis
)
from kanka_agent.config import GENERATED_SYSTEM_DIR

# Import des fonctions de compression d'images
from kanka_image import smart_compress_folder, smart_create_tokens

# Configuration de la page
st.set_page_config(
    page_title="Kanka Utils",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour améliorer l'apparence
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF6B6B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        color: #4ECDC4;
        border-bottom: 2px solid #4ECDC4;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #D4F1D4;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #28A745;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #F8D7DA;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #DC3545;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def get_available_systems() -> List[str]:
    """Récupère la liste des systèmes disponibles dans le dossier generated."""
    if not os.path.exists(GENERATED_SYSTEM_DIR):
        return []
    
    systems = []
    for file in os.listdir(GENERATED_SYSTEM_DIR):
        if file.endswith('.json'):
            systems.append(file[:-5])  # Enlever l'extension .json
    return sorted(systems)

def show_success(message: str):
    """Affiche un message de succès."""
    st.markdown(f'<div class="success-box">✅ {message}</div>', unsafe_allow_html=True)

def show_error(message: str):
    """Affiche un message d'erreur."""
    st.markdown(f'<div class="error-box">❌ {message}</div>', unsafe_allow_html=True)

def main():
    # Titre principal
    st.markdown('<h1 class="main-header">🌟 Kanka Utils</h1>', unsafe_allow_html=True)
    st.markdown("**Interface de gestion pour votre campagne Kanka et génération de contenu IA**")
    
    # Sidebar pour la navigation
    st.sidebar.title("📋 Navigation")
    page = st.sidebar.selectbox(
        "Choisissez une section",
        [
            "🏠 Accueil",
            "📚 Base de connaissance", 
            "🌌 Réseau FTL",
            "🖼 Compression Images",
            "�🚀 Génération",
            "📥 Import/Export",
            "✨ Enrichissement",
            "🔗 Synthèse"
        ]
    )
    
    # Page Accueil
    if page == "🏠 Accueil":
        st.markdown('<h2 class="section-header">Bienvenue dans Kanka Utils</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 Fonctionnalités principales")
            st.markdown("""
            - **📚 Base de connaissance** : Mise à jour automatique depuis vos exports Kanka
            - **🚀 Génération IA** : Création de systèmes et structures avec GPT-4
            - **📥 Import/Export** : Synchronisation bidirectionnelle avec Kanka
            - **✨ Enrichissement** : Amélioration du contenu existant
            - **🔗 Synthèse** : Génération automatique de résumés avec liens
            """)
        
        with col2:
            st.markdown("### 📊 Statistiques")
            available_systems = get_available_systems()
            st.metric("Systèmes disponibles", len(available_systems))
            
            if os.path.exists("rag_index.json"):
                st.metric("Index RAG", "✅ Actif")
            else:
                st.metric("Index RAG", "❌ Absent")
    
    # Page Base de connaissance
    elif page == "📚 Base de connaissance":
        st.markdown('<h2 class="section-header">📚 Gestion de la base de connaissance</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        La base de connaissance est utilisée par l'IA pour générer du contenu cohérent avec votre univers.
        Elle est construite à partir de vos exports Kanka et peut être exportée en différents formats.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔄 Mise à jour complète")
            if st.button("Mettre à jour la base de connaissance", use_container_width=True):
                with st.spinner("Mise à jour en cours... Cela peut prendre quelques minutes."):
                    try:
                        update_knowledge_base()
                        show_success("Base de connaissance mise à jour avec succès !")
                        show_success("Tous les formats ont été générés : JSON, JSONL, PDF, Markdown")
                        st.rerun()
                    except Exception as e:
                        show_error(f"Erreur lors de la mise à jour : {str(e)}")
                        st.error(traceback.format_exc())
        
        with col2:
            st.markdown("#### 📤 Exports disponibles")
            
            # Vérifier quels fichiers existent
            files_status = {
                "JSON": os.path.exists("univers_eneria_filtered.json"),
                "JSONL": os.path.exists("univers_eneria_connaissance_privee.jsonl"),
                "PDF": os.path.exists("univers_eneria_connaissance_privee.pdf"),
                "Markdown": os.path.exists("univers_eneria_connaissance.md"),
                "Réseau FTL": os.path.exists("univers_eneria_reseau_ftl.json")
            }
            
            for format_name, exists in files_status.items():
                if exists:
                    st.success(f"✅ {format_name}")
                else:
                    st.warning(f"❌ {format_name}")
        
        # Section dédiée au Markdown pour GPT
        st.markdown("---")
        st.markdown("#### 🤖 Export spécial pour GPT Custom")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            **Format Markdown optimisé pour les GPT** :
            - Structure hiérarchique claire avec titres et sous-titres
            - Conversion du HTML en Markdown propre
            - Organisation par catégories (Systèmes, Planètes, Organisations, etc.)
            - Nettoyage des caractères spéciaux et balises Kanka
            - Idéal pour alimenter un GPT custom avec votre univers
            """)
            
            if os.path.exists("univers_eneria_connaissance.md"):
                # Obtenir la taille du fichier
                file_size = os.path.getsize("univers_eneria_connaissance.md")
                size_kb = file_size / 1024
                st.metric("Taille du fichier Markdown", f"{size_kb:.1f} KB")
        
        with col2:
            if st.button("📋 Copier le chemin du fichier", use_container_width=True):
                if os.path.exists("univers_eneria_connaissance.md"):
                    file_path = os.path.abspath("univers_eneria_connaissance.md")
                    st.code(file_path, language="text")
                    st.info("📋 Chemin copié ! Utilisez ce fichier pour alimenter votre GPT custom.")
                else:
                    st.warning("Fichier Markdown non trouvé. Effectuez d'abord une mise à jour.")
            
            if os.path.exists("univers_eneria_connaissance.md"):
                # Bouton de téléchargement
                with open("univers_eneria_connaissance.md", "r", encoding="utf-8") as f:
                    markdown_content = f.read()
                
                st.download_button(
                    label="⬇️ Télécharger Markdown",
                    data=markdown_content,
                    file_name="univers_eneria_connaissance.md",
                    mime="text/markdown",
                    use_container_width=True
                )
        
        # Informations supplémentaires
        st.markdown("---")
        st.info("💡 **Conseils pour GPT Custom** : Uploadez le fichier Markdown dans les 'Knowledge' de votre GPT. Il contiendra toutes les informations sur votre univers d'Eneria pour des générations cohérentes.")
        
        # Section dédiée au réseau FTL
        st.markdown("---")
        st.markdown("#### 🌌 Réseau FTL - Base de données spécialisée")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            **Base de données du réseau de transport FTL** :
            - Toutes les connexions entre systèmes stellaires
            - Données structurées pour analyse de graphe
            - Informations sur les distances et statuts des liaisons
            - Format compatible avec les outils de visualisation réseau
            - Idéal pour l'analyse de connectivité et la planification de routes
            """)
            
            if os.path.exists("univers_eneria_reseau_ftl.json"):
                # Afficher les statistiques du réseau
                import json
                try:
                    with open("univers_eneria_reseau_ftl.json", "r", encoding="utf-8") as f:
                        ftl_data = json.load(f)
                    
                    col1a, col1b, col1c = st.columns(3)
                    with col1a:
                        st.metric("Systèmes", len(ftl_data.get("systems", {})))
                    with col1b:
                        st.metric("Connexions", len(ftl_data.get("connections", [])))
                    with col1c:
                        # Système le plus connecté
                        if ftl_data.get("systems"):
                            most_connected = max(ftl_data["systems"].items(), 
                                               key=lambda x: x[1]["connections_count"])
                            st.metric("Hub principal", f"{most_connected[0]} ({most_connected[1]['connections_count']})")
                except:
                    st.warning("Erreur lors du chargement des statistiques FTL")
        
        with col2:
            if os.path.exists("univers_eneria_reseau_ftl.json"):
                # Bouton de téléchargement pour le réseau FTL
                with open("univers_eneria_reseau_ftl.json", "r", encoding="utf-8") as f:
                    ftl_content = f.read()
                
                st.download_button(
                    label="⬇️ Télécharger Réseau FTL",
                    data=ftl_content,
                    file_name="univers_eneria_reseau_ftl.json",
                    mime="application/json",
                    use_container_width=True
                )
                
                file_size = os.path.getsize("univers_eneria_reseau_ftl.json")
                size_kb = file_size / 1024
                st.metric("Taille fichier", f"{size_kb:.1f} KB")
            else:
                st.warning("Fichier réseau FTL non trouvé. Effectuez d'abord une mise à jour.")
    
    # Page Réseau FTL
    elif page == "🌌 Réseau FTL":
        # Importer et exécuter la page du réseau FTL
        try:
            from pages.reseau_ftl import main as ftl_main  # type: ignore
            ftl_main()
        except ImportError as e:
            st.error(f"❌ Erreur d'import de la page Réseau FTL: {e}")
            st.info("Assurez-vous que le fichier `pages/reseau_ftl.py` existe.")
        except Exception as e:
            st.error(f"❌ Erreur lors de l'affichage du réseau FTL: {e}")
            st.exception(e)
    
    # Page Compression Images
    elif page == "🖼 Compression Images":
        st.markdown('<h2 class="section-header">🖼 Compression intelligente d\'images</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        **Compressez automatiquement vos images PNG** pour réduire leur taille tout en conservant une qualité optimale.
        
        - ✅ **Intelligent** : Ne retraite pas les images déjà compressées
        - ✅ **Sûr** : Préserve vos fichiers originaux  
        - ✅ **Automatique** : Ajoute `@0.5x` au nom des fichiers compressés
        """)
        
        # Interface de sélection du dossier
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📁 Sélection du dossier")
            
            # Zone de saisie pour le chemin
            folder_path = st.text_input(
                "Chemin vers le dossier d'images",
                placeholder="/Users/berard/Pictures/mes_images",
                help="Entrez le chemin complet vers le dossier contenant vos images PNG"
            )
            
            # Navigation par dossiers
            st.markdown("**Navigation rapide :**")
            
            # Dossiers communs en colonnes
            col_nav1, col_nav2, col_nav3 = st.columns(3)
            
            with col_nav1:
                if st.button("🏠 Accueil", use_container_width=True):
                    folder_path = str(Path.home())
                    st.rerun()
                
                if st.button("🖼️ Images", use_container_width=True):
                    folder_path = str(Path.home() / "Pictures")
                    st.rerun()
            
            with col_nav2:
                if st.button("🖥️ Bureau", use_container_width=True):
                    folder_path = str(Path.home() / "Desktop")
                    st.rerun()
                
                if st.button("📁 Documents", use_container_width=True):
                    folder_path = str(Path.home() / "Documents")
                    st.rerun()
            
            with col_nav3:
                if st.button("📥 Téléchargements", use_container_width=True):
                    folder_path = str(Path.home() / "Downloads")
                    st.rerun()
                
                if st.button("💿 Applications", use_container_width=True):
                    folder_path = "/Applications"
                    st.rerun()
            
            # Navigation dans le dossier actuel
            if folder_path and Path(folder_path).exists() and Path(folder_path).is_dir():
                current_path = Path(folder_path)
                
                # Bouton pour remonter au parent
                if current_path.parent != current_path:  # Pas à la racine
                    if st.button(f"⬆️ Dossier parent: {current_path.parent.name}", use_container_width=True):
                        folder_path = str(current_path.parent)
                        st.rerun()
                
                # Afficher les sous-dossiers
                try:
                    subdirs = [d for d in current_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
                    if subdirs:
                        st.markdown("**Sous-dossiers disponibles :**")
                        
                        # Limiter l'affichage pour ne pas surcharger l'interface
                        max_display = 8
                        cols_per_row = 2
                        
                        for i in range(0, min(len(subdirs), max_display), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j, col in enumerate(cols):
                                if i + j < len(subdirs) and i + j < max_display:
                                    subdir = subdirs[i + j]
                                    with col:
                                        if st.button(f"� {subdir.name}", use_container_width=True, key=f"subdir_{i+j}"):
                                            folder_path = str(subdir)
                                            st.rerun()
                        
                        if len(subdirs) > max_display:
                            st.info(f"... et {len(subdirs) - max_display} autres dossiers")
                except PermissionError:
                    st.warning("⚠️ Accès refusé à ce dossier")
                except Exception as e:
                    st.warning(f"⚠️ Erreur lors de la lecture du dossier: {str(e)}")
            
            # Chemin rapide par saisie directe
            with st.expander("✏️ Chemins personnalisés"):
                st.markdown("**Dossiers fréquemment utilisés :**")
                
                common_paths = [
                    ("🎮 Dossier Jeux", "/Users/berard/Documents/Jeux"),
                    ("🛠️ Dossier Outils", "/Users/berard/Documents/Outils"),
                    ("📷 Photos", "/Users/berard/Pictures/Photos"),
                    ("🎨 Illustrations", "/Users/berard/Pictures/Illustrations"),
                ]
                
                for name, path in common_paths:
                    if Path(path).exists():
                        if st.button(name, use_container_width=True, key=f"custom_{path}"):
                            folder_path = path
                            st.rerun()
                
                # Saisie manuelle avancée
                custom_path = st.text_input(
                    "Ou saisissez un chemin personnalisé:",
                    placeholder="/Volumes/MonDisque/MesImages",
                    key="custom_path_input"
                )
                if custom_path and st.button("➡️ Aller à ce dossier"):
                    folder_path = custom_path
                    st.rerun()
        
        with col2:
            st.markdown("### ⚙️ Paramètres")
            
            scale_factor = st.slider(
                "Facteur de redimensionnement",
                min_value=0.1,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="0.5 = 50% de la taille originale"
            )
            
            palette_size = st.selectbox(
                "Nombre de couleurs max",
                [256, 128, 64, 32, 16],
                index=0,
                help="Moins de couleurs = plus de compression"
            )
            
            overwrite = st.checkbox(
                "Remplacer les fichiers existants",
                value=False,
                help="⚠️ Attention: remplace les versions @{scale}x existantes"
            )
        
        # Vérification du dossier
        if folder_path:
            folder_path_obj = Path(folder_path)
            
            # Affichage du chemin actuel avec navigation par segments
            st.markdown("**Chemin actuel :**")
            path_parts = folder_path_obj.parts
            if len(path_parts) > 1:
                breadcrumb_cols = st.columns(min(len(path_parts), 6))  # Limiter à 6 segments
                
                for i, (part, col) in enumerate(zip(path_parts[-6:], breadcrumb_cols)):
                    with col:
                        # Construire le chemin jusqu'à ce segment
                        if i == 0 and len(path_parts) > 6:
                            # Afficher "..." pour les parties tronquées
                            segment_path = "/" + "/".join(path_parts[-6+i:])
                            display_name = "..."
                        else:
                            segment_path = "/" + "/".join(path_parts[:len(path_parts)-6+i+1]) if len(path_parts) > 6 else "/" + "/".join(path_parts[:len(path_parts)-len(breadcrumb_cols)+i+1])
                            display_name = part if part else "/"
                        
                        if st.button(display_name, key=f"breadcrumb_{i}", use_container_width=True):
                            if Path(segment_path).exists():
                                folder_path = segment_path
                                st.rerun()
            
            if folder_path_obj.exists() and folder_path_obj.is_dir():
                # Compter les fichiers PNG
                png_files = list(folder_path_obj.glob("*.png"))
                st.success(f"✅ Dossier valide : {len(png_files)} fichiers PNG trouvés")
                
                if png_files:
                    # Afficher quelques exemples
                    st.markdown("**Aperçu des fichiers :**")
                    for i, png_file in enumerate(png_files[:5]):
                        size_kb = png_file.stat().st_size / 1024
                        st.text(f"• {png_file.name} ({size_kb:.1f} KB)")
                    
                    if len(png_files) > 5:
                        st.text(f"... et {len(png_files) - 5} autres fichiers")
                
            elif folder_path_obj.exists():
                st.error("❌ Ce chemin n'est pas un dossier")
            else:
                st.error("❌ Ce dossier n'existe pas")
        
        # Bouton de compression
        st.markdown("---")
        
        if folder_path and Path(folder_path).exists():
            col_btn, col_info = st.columns([1, 2])
            
            with col_btn:
                if st.button("🚀 Lancer la compression", type="primary", use_container_width=True):
                    # Exécuter la compression
                    with st.spinner("🔄 Compression en cours..."):
                        try:
                            resultats = smart_compress_folder(
                                folder_path,
                                scale_factor=scale_factor,
                                palette_size=palette_size,
                                overwrite=overwrite
                            )
                            
                            # Afficher les résultats
                            if resultats['success']:
                                st.success("🎉 Compression terminée avec succès !")
                                
                                # Métriques
                                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                                
                                with col_m1:
                                    st.metric("Images trouvées", resultats['total_found'])
                                
                                with col_m2:
                                    st.metric("Images traitées", len(resultats['processed']))
                                
                                with col_m3:
                                    st.metric("Images ignorées", len(resultats['skipped']))
                                
                                with col_m4:
                                    if resultats['processed']:
                                        st.metric("Réduction", f"{resultats['overall_reduction']:.1f}%")
                                    else:
                                        st.metric("Réduction", "0%")
                                
                                # Détails
                                if resultats['processed']:
                                    st.markdown("### ✅ Images compressées")
                                    for item in resultats['processed']:
                                        original_size = item['original_size'] / 1024
                                        compressed_size = item['compressed_size'] / 1024
                                        reduction = item['reduction_percent']
                                        st.text(f"• {Path(item['original']).name} → {Path(item['compressed']).name}")
                                        st.text(f"  {original_size:.1f} KB → {compressed_size:.1f} KB (-{reduction:.1f}%)")
                                
                                if resultats['skipped']:
                                    with st.expander(f"📝 Images ignorées ({len(resultats['skipped'])})"):
                                        for item in resultats['skipped']:
                                            st.text(f"• {Path(item['original']).name} (déjà compressé)")
                                
                                if resultats['errors']:
                                    st.markdown("### ❌ Erreurs")
                                    for error in resultats['errors']:
                                        st.error(f"• {error}")
                            
                            else:
                                st.error("❌ Erreur durant la compression")
                        
                        except Exception as e:
                            st.error(f"❌ Erreur: {str(e)}")
                            st.exception(e)
            
            with col_info:
                st.info(f"""
                **Configuration actuelle :**
                - Redimensionnement : {int(scale_factor * 100)}%
                - Couleurs max : {palette_size}
                - Suffixe : @{scale_factor}x
                - Remplacer : {'Oui' if overwrite else 'Non'}
                """)
        
        else:
            st.warning("👆 Veuillez d'abord sélectionner un dossier valide")
        
        # Guide d'utilisation
        with st.expander("📖 Guide d'utilisation"):
            st.markdown("""
            ### Comment utiliser la compression intelligente
            
            1. **Sélectionnez un dossier** contenant vos images PNG
            2. **Ajustez les paramètres** selon vos besoins :
               - **Facteur de redimensionnement** : 0.5 = 50% de la taille originale
               - **Nombre de couleurs** : moins de couleurs = plus de compression
            3. **Cliquez sur "Lancer la compression"**
            
            ### Ce qui se passe
            - Les images originales ne sont **jamais modifiées**
            - Les versions compressées sont créées avec le suffixe `@{factor}x`
            - Exemple : `photo.png` → `photo@0.5x.png`
            - Si une version compressée existe déjà, elle est ignorée (sauf si "Remplacer" est coché)
            
            ### Conseils
            - Commencez avec les paramètres par défaut (50%, 256 couleurs)
            - Pour une compression plus agressive, utilisez 30% et 64 couleurs
            - Les images sont optimisées pour le web avec une palette de couleurs réduite
            """)
        
        # Section Tokens circulaires
        st.markdown("---")
        st.markdown('<h3 class="section-header">🎯 Création de tokens circulaires</h3>', unsafe_allow_html=True)
        
        st.markdown("""
        Cette fonctionnalité crée des tokens circulaires à partir de vos images compressées, 
        parfaits pour représenter des personnages ou objets dans vos campagnes.
        """)
        
        # Configuration des tokens
        col_token1, col_token2 = st.columns(2)
        
        with col_token1:
            token_scale = st.selectbox(
                "Taille du token",
                options=[0.3, 0.4, 0.5, 0.6],
                index=2,
                format_func=lambda x: f"{int(x*100)}% de l'image source",
                help="Taille finale du token par rapport à l'image compressée source"
            )
        
        with col_token2:
            source_suffix = st.selectbox(
                "Images sources",
                options=["@0.5x", "@0.3x", "@0.7x", "original"],
                index=0,
                help="Quelles images utiliser comme source pour créer les tokens"
            )
        
        # Bouton de création des tokens
        if folder_path and Path(folder_path).exists():
            col_btn_token, col_info_token = st.columns([1, 2])
            
            with col_btn_token:
                if st.button("🎯 Créer les tokens", type="secondary", use_container_width=True):
                    # Créer les tokens
                    with st.spinner("🔄 Création des tokens en cours..."):
                        try:
                            # Adapter le suffixe
                            suffix_to_use = "" if source_suffix == "original" else source_suffix
                            
                            resultats_tokens = smart_create_tokens(
                                folder_path,
                                scale_factor=token_scale,
                                source_suffix=suffix_to_use
                            )
                            
                            # Afficher les résultats
                            if "error" not in resultats_tokens:
                                st.success("🎉 Tokens créés avec succès !")
                                
                                # Métriques
                                col_tm1, col_tm2, col_tm3 = st.columns(3)
                                
                                with col_tm1:
                                    st.metric("Tokens créés", len(resultats_tokens['processed']))
                                
                                with col_tm2:
                                    st.metric("Tokens ignorés", len(resultats_tokens['skipped']))
                                
                                with col_tm3:
                                    st.metric("Erreurs", len(resultats_tokens['errors']))
                                
                                # Détails
                                if resultats_tokens['processed']:
                                    st.markdown("### ✅ Tokens créés")
                                    for token_path in resultats_tokens['processed']:
                                        token_name = Path(token_path).name
                                        st.text(f"• {token_name}")
                                
                                if resultats_tokens['skipped']:
                                    with st.expander(f"📝 Tokens ignorés ({len(resultats_tokens['skipped'])})"):
                                        for token_path in resultats_tokens['skipped']:
                                            token_name = Path(token_path).name
                                            st.text(f"• {token_name} (déjà existant)")
                                
                                if resultats_tokens['errors']:
                                    st.markdown("### ❌ Erreurs")
                                    for error in resultats_tokens['errors']:
                                        st.error(f"• {error}")
                            
                            else:
                                st.error(f"❌ {resultats_tokens['error']}")
                        
                        except Exception as e:
                            st.error(f"❌ Erreur: {str(e)}")
                            st.exception(e)
            
            with col_info_token:
                st.info(f"""
                **Configuration tokens :**
                - Source : Images {source_suffix if source_suffix != 'original' else 'originales'}
                - Taille token : {int(token_scale * 100)}%
                - Format : _round@{token_scale}x.png
                - Traitement : Carré + Cercle + Transparence
                """)
        
        else:
            st.warning("👆 Veuillez d'abord sélectionner un dossier valide")
        
        # Guide d'utilisation des tokens
        with st.expander("📖 Guide des tokens circulaires"):
            st.markdown("""
            ### Comment ça fonctionne
            
            1. **Sélection des images sources** : Le système utilise vos images compressées
            2. **Transformation en carré** : L'image est recadrée en gardant la partie supérieure
            3. **Création du cercle** : Seule la partie centrale circulaire est conservée
            4. **Transparence** : Tout ce qui est hors du cercle devient transparent
            5. **Redimensionnement** : Le token est redimensionné selon votre choix
            
            ### Utilisation recommandée
            - **Personnages** : Portraits qui s'adapteront parfaitement en rond
            - **Objets** : Items, armes, équipements centrés
            - **Tokens de combat** : Parfaits pour les plateaux de jeu
            
            ### Noms des fichiers
            - Si l'image source est `hero@0.5x.png`
            - Le token sera `hero_round@{token_scale}x.png`
            """)

    # Page Génération
    elif page == "🚀 Génération":
        st.markdown('<h2 class="section-header">🚀 Génération de contenu IA</h2>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🌌 Systèmes stellaires", "🏗️ Structures"])
        
        with tab1:
            st.markdown("### Générer un nouveau système stellaire")
            
            col1, col2 = st.columns(2)
            with col1:
                system_name = st.text_input("Nom du système (optionnel)", placeholder="Ex: Proxima, Alpha Centauri...")
            with col2:
                system_context = st.text_area("Contexte (optionnel)", placeholder="Ex: Système hostile, riche en minerais...")
            
            if st.button("🌟 Générer le système", use_container_width=True):
                with st.spinner("Génération en cours... L'IA analyse votre univers et crée le système."):
                    try:
                        context_list = [system_context] if system_context else None
                        generate_system(system_name, context_list)
                        show_success(f"Système '{system_name or 'généré'}' créé et importé dans Kanka !")
                        st.rerun()
                    except Exception as e:
                        show_error(f"Erreur lors de la génération : {str(e)}")
                        st.error(traceback.format_exc())
        
        with tab2:
            st.markdown("### Générer une structure artificielle")
            
            col1, col2 = st.columns(2)
            with col1:
                structure_name = st.text_input("Nom de la structure (optionnel)", placeholder="Ex: Station Omega, Colonie Zeta...")
                structure_type = st.selectbox("Type de structure", 
                    ["", "Station", "Colonie", "Ruines", "Ville", "Debrits spaciaux"])
            with col2:
                structure_context = st.text_area("Contexte (optionnel)", placeholder="Ex: Station de recherche, colonie minière...")
                structure_location = st.text_input("Emplacement parent (optionnel)", placeholder="Ex: Proxima III, Ceinture d'astéroïdes...")
            
            if st.button("🏗️ Générer la structure", use_container_width=True):
                with st.spinner("Génération en cours..."):
                    try:
                        context_list = [structure_context] if structure_context else None
                        generate_structure(structure_name, structure_type, context_list, structure_location)
                        show_success(f"Structure '{structure_name or 'générée'}' créée et importée dans Kanka !")
                        st.rerun()
                    except Exception as e:
                        show_error(f"Erreur lors de la génération : {str(e)}")
                        st.error(traceback.format_exc())
    
    # Page Import/Export
    elif page == "📥 Import/Export":
        st.markdown('<h2 class="section-header">📥 Import/Export Kanka</h2>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["📤 Export depuis Kanka", "📤 Import vers Kanka"])
        
        with tab1:
            st.markdown("### Exporter depuis Kanka")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Exporter un système spécifique")
                location_id = st.number_input("ID Kanka du système", min_value=1, step=1, value=1757369)
                if st.button("📥 Exporter ce système", use_container_width=True):
                    with st.spinner("Export en cours..."):
                        try:
                            export_system_from_kanka(location_id)
                            show_success(f"Système (ID: {location_id}) exporté avec succès !")
                            st.rerun()
                        except Exception as e:
                            show_error(f"Erreur lors de l'export : {str(e)}")
            
            with col2:
                st.markdown("#### Exporter tous les systèmes")
                st.warning("⚠️ Cette opération peut prendre du temps selon le nombre de systèmes.")
                if st.button("📥 Exporter tous les systèmes", use_container_width=True):
                    
                    # Conteneurs pour la progression
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        def update_progress(current, total, message):
                            if total > 0:
                                progress = current / total
                                progress_bar.progress(progress)
                            status_text.text(f"{message} ({current}/{total})")
                        
                        export_all_systems_with_progress(update_progress)
                        
                        # Finaliser
                        progress_bar.progress(1.0)
                        status_text.empty()
                        show_success("Tous les systèmes ont été exportés !")
                        st.rerun()
                        
                    except Exception as e:
                        progress_bar.empty()
                        status_text.empty()
                        show_error(f"Erreur lors de l'export : {str(e)}")
        
        with tab2:
            st.markdown("### Importer vers Kanka")
            
            available_systems = get_available_systems()
            
            if available_systems:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Importer un système")
                    selected_system = st.selectbox("Choisir un système", available_systems)
                    if st.button("📤 Importer le système", use_container_width=True):
                        with st.spinner(f"Import de {selected_system} vers Kanka..."):
                            try:
                                import_system(selected_system)
                                show_success(f"Système '{selected_system}' importé dans Kanka !")
                            except Exception as e:
                                show_error(f"Erreur lors de l'import : {str(e)}")
                
                with col2:
                    st.markdown("#### Importer une location")
                    selected_location = st.selectbox("Choisir une location", available_systems, key="location_select")
                    parent_id = st.number_input("ID parent (optionnel)", min_value=0, step=1, value=0, key="parent_id")
                    if st.button("📤 Importer la location", use_container_width=True):
                        with st.spinner(f"Import de {selected_location} vers Kanka..."):
                            try:
                                parent = parent_id if parent_id > 0 else None
                                import_location(selected_location, parent)
                                show_success(f"Location '{selected_location}' importée dans Kanka !")
                            except Exception as e:
                                show_error(f"Erreur lors de l'import : {str(e)}")
            else:
                st.info("Aucun système disponible. Générez ou exportez d'abord des systèmes.")
    
    # Page Enrichissement
    elif page == "✨ Enrichissement":
        st.markdown('<h2 class="section-header">✨ Enrichissement de contenu</h2>', unsafe_allow_html=True)
        
        available_systems = get_available_systems()
        
        if available_systems:
            tab1, tab2 = st.tabs(["🌌 Enrichir un système", "🏗️ Enrichir une structure"])
            
            with tab1:
                st.markdown("### Enrichir un système existant")
                
                col1, col2 = st.columns(2)
                with col1:
                    selected_system = st.selectbox("Choisir un système", available_systems, key="enrich_system")
                    enrich_prompt = st.text_area("Instructions d'enrichissement", 
                        placeholder="Ex: Ajoute une planète océanique, enrichis les descriptions des astéroïdes...")
                
                with col2:
                    enrich_context = st.text_area("Contexte supplémentaire (optionnel)", 
                        placeholder="Ex: Guerre récente, découverte archéologique...")
                
                if st.button("✨ Enrichir le système", use_container_width=True):
                    if enrich_prompt:
                        with st.spinner("Enrichissement en cours..."):
                            try:
                                context_list = [enrich_context] if enrich_context else None
                                enrich_system(selected_system, enrich_prompt, context_list)
                                show_success(f"Système '{selected_system}' enrichi avec succès !")
                            except Exception as e:
                                show_error(f"Erreur lors de l'enrichissement : {str(e)}")
                    else:
                        show_error("Veuillez fournir des instructions d'enrichissement.")
            
            with tab2:
                st.markdown("### Enrichir une structure existante")
                
                col1, col2 = st.columns(2)
                with col1:
                    selected_structure = st.selectbox("Choisir une structure", available_systems, key="enrich_structure")
                    structure_prompt = st.text_area("Instructions d'enrichissement", 
                        placeholder="Ex: Ajoute des détails sur les habitants, décris les technologies utilisées...")
                
                with col2:
                    structure_context = st.text_area("Contexte supplémentaire (optionnel)", 
                        placeholder="Ex: Récente expansion, problèmes techniques...")
                    structure_location = st.text_input("Emplacement (optionnel)", 
                        placeholder="Ex: Orbite de Mars, surface de Titan...")
                
                if st.button("✨ Enrichir la structure", use_container_width=True):
                    if structure_prompt:
                        with st.spinner("Enrichissement en cours..."):
                            try:
                                context_list = [structure_context] if structure_context else None
                                enrich_structure(selected_structure, structure_prompt, context_list, structure_location)
                                show_success(f"Structure '{selected_structure}' enrichie avec succès !")
                            except Exception as e:
                                show_error(f"Erreur lors de l'enrichissement : {str(e)}")
                    else:
                        show_error("Veuillez fournir des instructions d'enrichissement.")
        else:
            st.info("Aucun système disponible. Générez ou exportez d'abord des systèmes.")
    
    # Page Synthèse
    elif page == "🔗 Synthèse":
        st.markdown('<h2 class="section-header">🔗 Génération de synthèse</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        La synthèse génère automatiquement un résumé du système avec des liens Kanka vers les éléments importants.
        **Important** : Le système doit avoir été exporté depuis Kanka pour avoir les `entity_id` nécessaires aux liens.
        """)
        
        available_systems = get_available_systems()
        
        if available_systems:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                selected_system = st.selectbox("Choisir un système", available_systems, key="synthesis_system")
                
                # Vérifier si le système a un ID Kanka
                try:
                    json_path = os.path.join(GENERATED_SYSTEM_DIR, f"{selected_system}.json")
                    with open(json_path, "r", encoding="utf-8") as f:
                        system_data = json.load(f)
                    
                    has_kanka_id = "id" in system_data
                    if has_kanka_id:
                        st.success(f"✅ Système avec ID Kanka : {system_data['id']}")
                    else:
                        st.warning("⚠️ Ce système n'a pas d'ID Kanka. Exportez-le d'abord depuis Kanka.")
                except:
                    st.error("❌ Impossible de lire le fichier du système.")
                    has_kanka_id = False
            
            with col2:
                st.markdown("### Actions disponibles")
                
                # Bouton unique pour le workflow complet
                if st.button("🔄 Générer synthèse (Export + Génération + Import)", use_container_width=True):
                    if has_kanka_id:
                        with st.spinner("Exécution du workflow complet..."):
                            try:
                                generate_system_synthesis(selected_system)
                                show_success("Synthèse générée et mise à jour dans Kanka !")
                            except Exception as e:
                                show_error(f"Erreur lors du workflow : {str(e)}")
                    else:
                        show_error("Le système doit avoir un ID Kanka pour générer une synthèse.")
        else:
            st.info("Aucun système disponible. Générez ou exportez d'abord des systèmes.")
    
    # Sidebar - Informations système
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Informations")
    
    available_systems = get_available_systems()
    st.sidebar.metric("Systèmes locaux", len(available_systems))
    
    if available_systems:
        st.sidebar.markdown("#### Systèmes disponibles:")
        for system in available_systems[:5]:  # Afficher seulement les 5 premiers
            st.sidebar.markdown(f"• {system}")
        if len(available_systems) > 5:
            st.sidebar.markdown(f"• ... et {len(available_systems) - 5} autres")

if __name__ == "__main__":
    main()
