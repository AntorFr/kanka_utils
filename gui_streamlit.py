import streamlit as st
import os
import json
import traceback
from typing import Optional, List

# Import des fonctions du main
from main import (
    update_knowledge_base, generate_system, generate_structure, 
    export_system_from_kanka, export_all_systems, import_system,
    import_location, import_characters, enrich_system, enrich_structure,
    generate_system_synthesis
)
from kanka_agent.config import GENERATED_SYSTEM_DIR

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
            "🚀 Génération",
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
                "Markdown": os.path.exists("univers_eneria_connaissance.md")
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
                    with st.spinner("Export de tous les systèmes en cours..."):
                        try:
                            export_all_systems()
                            show_success("Tous les systèmes ont été exportés !")
                            st.rerun()
                        except Exception as e:
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
                
                # Workflow complet
                if st.button("🔄 Workflow complet (Export + Synthèse + Import)", use_container_width=True):
                    if has_kanka_id:
                        with st.spinner("Exécution du workflow complet..."):
                            try:
                                # 1. Export depuis Kanka
                                st.info("1/3 - Export depuis Kanka...")
                                export_system_from_kanka(system_data['id'])
                                
                                # 2. Génération de synthèse
                                st.info("2/3 - Génération de la synthèse...")
                                generate_system_synthesis(selected_system)
                                
                                # 3. Import vers Kanka
                                st.info("3/3 - Import vers Kanka...")
                                import_system(selected_system)
                                
                                show_success("Workflow complet terminé ! Le système a été mis à jour dans Kanka avec sa synthèse.")
                            except Exception as e:
                                show_error(f"Erreur lors du workflow : {str(e)}")
                    else:
                        show_error("Le système doit avoir un ID Kanka pour le workflow complet.")
                
                # Synthèse seule
                if st.button("✨ Générer synthèse uniquement", use_container_width=True):
                    if has_kanka_id:
                        with st.spinner("Génération de la synthèse..."):
                            try:
                                generate_system_synthesis(selected_system)
                                show_success(f"Synthèse générée pour '{selected_system}' !")
                            except Exception as e:
                                show_error(f"Erreur lors de la génération : {str(e)}")
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

st.title("🚀 Kanka Utils - Interface de Gestion")
st.markdown("Interface graphique pour gérer vos systèmes stellaires et structures dans Kanka")

# Sidebar pour la navigation
st.sidebar.title("📋 Actions")
action = st.sidebar.selectbox(
    "Choisissez une action:",
    [
        "📚 Mise à jour base de connaissance",
        "🌟 Générer un système stellaire",
        "🏗️ Générer une structure",
        "📤 Exporter depuis Kanka",
        "📥 Importer vers Kanka",
        "✨ Enrichir un système",
        "🔄 Générer une synthèse",
        "👥 Gestion des personnages"
    ]
)

# Fonction utilitaire pour lister les systèmes existants
def get_existing_systems():
    """Récupère la liste des systèmes existants dans le dossier generated"""
    if not os.path.exists(GENERATED_SYSTEM_DIR):
        return []
    files = [f.replace('.json', '') for f in os.listdir(GENERATED_SYSTEM_DIR) if f.endswith('.json')]
    return files

# Interface selon l'action sélectionnée
if action == "📚 Mise à jour base de connaissance":
    st.header("📚 Mise à jour de la base de connaissance")
    st.markdown("Met à jour la base de connaissance locale et l'index RAG à partir du fichier ZIP.")
    
    if st.button("🔄 Mettre à jour la base de connaissance", type="primary"):
        with st.spinner("Mise à jour en cours..."):
            try:
                update_knowledge_base()
                st.success("✅ Base de connaissance mise à jour avec succès!")
            except Exception as e:
                st.error(f"❌ Erreur: {str(e)}")

elif action == "🌟 Générer un système stellaire":
    st.header("🌟 Génération d'un système stellaire")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nom_systeme = st.text_input("Nom du système (optionnel):", placeholder="Ex: Alpha Centauri")
        
    with col2:
        contexte = st.text_area("Contexte (optionnel):", placeholder="Ex: Système riche en ressources minières...")
    
    if st.button("🚀 Générer le système", type="primary"):
        with st.spinner("Génération en cours..."):
            try:
                generate_system(nom_systeme if nom_systeme else "", contexte if contexte else None)
                st.success(f"✅ Système '{nom_systeme}' généré et importé dans Kanka!")
            except Exception as e:
                st.error(f"❌ Erreur: {str(e)}")

elif action == "🏗️ Générer une structure":
    st.header("🏗️ Génération d'une structure artificielle")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nom_structure = st.text_input("Nom de la structure:", placeholder="Ex: Station Alpha")
        type_structure = st.selectbox("Type de structure:", 
                                    ["Station", "Colonie", "Ruines", "Ville", "Debrits spaciaux"])
        
    with col2:
        location = st.text_input("Emplacement parent:", placeholder="Ex: Aureon I")
        contexte_structure = st.text_area("Contexte:", placeholder="Ex: Centre de recherche...")
    
    if st.button("🏗️ Générer la structure", type="primary"):
        with st.spinner("Génération en cours..."):
            try:
                generate_structure(nom_structure, type_structure, contexte_structure if contexte_structure else None, location if location else "")
                st.success(f"✅ Structure '{nom_structure}' générée et importée!")
            except Exception as e:
                st.error(f"❌ Erreur: {str(e)}")

elif action == "📤 Exporter depuis Kanka":
    st.header("📤 Export depuis Kanka")
    
    tab1, tab2 = st.tabs(["Système spécifique", "Tous les systèmes"])
    
    with tab1:
        location_id = st.number_input("ID Kanka du système:", min_value=1, value=1757369)
        
        if st.button("📤 Exporter le système", type="primary"):
            with st.spinner("Export en cours..."):
                try:
                    export_system_from_kanka(location_id)
                    st.success("✅ Système exporté avec succès!")
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")
    
    with tab2:
        st.warning("⚠️ Cette opération peut prendre du temps selon le nombre de systèmes.")
        
        if st.button("📤 Exporter tous les systèmes", type="primary"):
            with st.spinner("Export de tous les systèmes..."):
                try:
                    export_all_systems()
                    st.success("✅ Tous les systèmes exportés!")
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")

elif action == "📥 Importer vers Kanka":
    st.header("📥 Import vers Kanka")
    
    systems = get_existing_systems()
    
    if not systems:
        st.warning("Aucun système trouvé. Générez ou exportez d'abord des systèmes.")
    else:
        selected_system = st.selectbox("Système à importer:", systems)
        
        if st.button("📥 Importer vers Kanka", type="primary"):
            with st.spinner("Import en cours..."):
                try:
                    import_system(selected_system)
                    st.success(f"✅ Système '{selected_system}' importé vers Kanka!")
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")

elif action == "✨ Enrichir un système":
    st.header("✨ Enrichissement d'un système")
    
    systems = get_existing_systems()
    
    if not systems:
        st.warning("Aucun système trouvé. Générez ou exportez d'abord des systèmes.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            selected_system = st.selectbox("Système à enrichir:", systems)
            
        with col2:
            contexte_enrich = st.text_area("Contexte supplémentaire:", placeholder="Ex: Nouvelles découvertes...")
        
        prompt_enrichissement = st.text_area("Instructions d'enrichissement:", 
                                           placeholder="Ex: Ajoute des lunes aux planètes existantes...")
        
        if st.button("✨ Enrichir le système", type="primary"):
            with st.spinner("Enrichissement en cours..."):
                try:
                    enrich_system(selected_system, prompt_enrichissement, contexte_enrich if contexte_enrich else None)
                    st.success(f"✅ Système '{selected_system}' enrichi!")
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")

elif action == "🔄 Générer une synthèse":
    st.header("🔄 Génération de synthèse")
    
    systems = get_existing_systems()
    
    if not systems:
        st.warning("Aucun système trouvé. Générez ou exportez d'abord des systèmes.")
    else:
        selected_system = st.selectbox("Système pour la synthèse:", systems)
        
        # Afficher un aperçu du système sélectionné
        if selected_system:
            try:
                json_path = os.path.join(GENERATED_SYSTEM_DIR, f"{selected_system}.json")
                with open(json_path, "r", encoding="utf-8") as f:
                    system_data = json.load(f)
                
                st.subheader("📋 Aperçu du système")
                st.markdown(f"**Nom:** {system_data.get('name', 'N/A')}")
                st.markdown(f"**Type:** {system_data.get('type', 'N/A')}")
                
                if 'contains' in system_data:
                    st.markdown(f"**Éléments contenus:** {len(system_data['contains'])}")
                    with st.expander("Voir les éléments"):
                        for element in system_data['contains']:
                            st.markdown(f"- {element.get('name', 'N/A')} ({element.get('type', 'N/A')})")
                
            except Exception as e:
                st.error(f"Erreur lors du chargement du système: {str(e)}")
        
        if st.button("🔄 Générer la synthèse", type="primary"):
            with st.spinner("Génération de la synthèse..."):
                try:
                    generate_system_synthesis(selected_system)
                    st.success(f"✅ Synthèse générée pour '{selected_system}'!")
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")

elif action == "👥 Gestion des personnages":
    st.header("👥 Gestion des personnages")
    st.info("🚧 Fonctionnalité en développement")
    
    # Placeholder pour futures fonctionnalités de personnages
    st.markdown("Fonctionnalités prévues:")
    st.markdown("- Import/Export de personnages")
    st.markdown("- Génération de personnages IA")
    st.markdown("- Gestion des relations entre personnages")

# Footer avec informations utiles
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Statistiques")

# Afficher le nombre de systèmes existants
systems_count = len(get_existing_systems())
st.sidebar.metric("Systèmes locaux", systems_count)

# Afficher l'état de la base de connaissance
if os.path.exists("rag_index.index"):
    st.sidebar.success("✅ Index RAG disponible")
else:
    st.sidebar.warning("⚠️ Index RAG manquant")

st.sidebar.markdown("---")
st.sidebar.markdown("**🛠️ Kanka Utils v1.0**")
st.sidebar.markdown("Interface de gestion pour campagnes Stars Without Number")
