"""
Page de visualisation du réseau FTL
Interface Streamlit pour afficher graphiquement les connexions FTL entre systèmes
"""

import streamlit as st
import json
import os
from streamlit_agraph import agraph, Node, Edge, Config
from typing import Dict, List, Tuple

def load_ftl_data():
    """Charge les données du réseau FTL depuis le fichier JSON"""
    ftl_file = os.path.join(os.path.dirname(__file__), "..", "univers_eneria_reseau_ftl.json")
    
    if not os.path.exists(ftl_file):
        st.error(f"❌ Fichier de données FTL non trouvé: {ftl_file}")
        return None
    
    try:
        with open(ftl_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données FTL: {e}")
        return None

def create_network_graph(data: Dict, show_private: bool = True, max_distance: int = None, node_size: int = 15) -> Tuple[List[Node], List[Edge]]:
    """
    Crée les nœuds et arêtes pour le graphique de réseau
    
    Args:
        data: Données FTL chargées depuis le JSON
        show_private: Si True, affiche les liens privés
    
    Returns:
        Tuple contenant (nodes, edges)
    """
    nodes = []
    edges = []
    
    # Créer les nœuds (systèmes)
    systems = data.get('systems', {})
    for system_name, system_data in systems.items():
        # Taille du nœud avec facteur de connexions mais contrôlée par le slider
        connections_count = system_data.get('connections_count', 0)
        size = node_size + (connections_count * 2)  # Taille de base + bonus pour connexions
        
        node = Node(
            id=system_name,
            label=system_name,
            size=size,
            color="#4A90E2",  # Bleu pour tous les systèmes
            font={"size": max(8, node_size // 2), "color": "#FFFFFF"},
            shape="dot"
        )
        nodes.append(node)
    
    # Créer les arêtes (connexions)
    connections = data.get('connections', [])
    edge_id = 0
    
    for conn in connections:
        # Vérifier si on doit afficher les liens privés
        is_private = conn.get('prive', False) or conn.get('status', '').lower().find('privée') >= 0
        if is_private and not show_private:
            continue
        
        # Filtrer par distance si spécifié
        distance = conn.get('distance', 5)
        if max_distance and distance > max_distance:
            continue
        
        # Couleur selon le type de connexion
        if is_private:
            color = "#FF6B6B"  # Rouge pour les liens privés
            width = 2
            dashes = True
        else:
            color = "#51CF66"  # Vert pour les liens répertoriés
            width = 3
            dashes = False
        
        # Largeur et longueur proportionnelles à la distance
        distance = conn.get('distance', 5)
        width = max(1, 6 - distance)  # Largeur inversement proportionnelle
        length = distance * 20  # Longueur proportionnelle à la distance
        
        edge = Edge(
            source=conn['source'],
            target=conn['target'],
            color=color,
            width=width,
            dashes=dashes,
            label=f"Distance: {distance}",
            font={"size": 10},
            length=length  # Contrôle la longueur visuelle de l'arête
        )
        edges.append(edge)
        edge_id += 1
    
    return nodes, edges

def show_network_stats(data: Dict, show_private: bool = True, max_distance: int = None):
    """Affiche les statistiques du réseau"""
    if not data:
        return
    
    metadata = data.get('metadata', {})
    systems = data.get('systems', {})
    connections = data.get('connections', [])
    
    # Filtrer les connexions selon l'affichage et la distance
    if show_private:
        visible_connections = connections
    else:
        visible_connections = [c for c in connections if not (c.get('prive', False) or c.get('status', '').lower().find('privée') >= 0)]
    
    # Filtrer par distance si spécifié
    if max_distance:
        visible_connections = [c for c in visible_connections if c.get('distance', 5) <= max_distance]
    
    # Statistiques de base
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🌟 Systèmes", len(systems))
    
    with col2:
        st.metric("🔗 Connexions visibles", len(visible_connections))
    
    with col3:
        public_count = len([c for c in connections if not (c.get('prive', False) or c.get('status', '').lower().find('privée') >= 0)])
        st.metric("📡 Liens répertoriés", public_count)
    
    with col4:
        private_count = len([c for c in connections if (c.get('prive', False) or c.get('status', '').lower().find('privée') >= 0)])
        st.metric("🔒 Liens privés", private_count)
    
    # Statistiques avancées
    if visible_connections:
        st.subheader("📊 Statistiques du réseau affiché")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Systèmes les plus connectés
            st.write("**Hubs principaux:**")
            sorted_systems = sorted(systems.items(), key=lambda x: x[1].get('connections_count', 0), reverse=True)
            for i, (name, data) in enumerate(sorted_systems[:5]):
                st.write(f"{i+1}. **{name}** - {data.get('connections_count', 0)} connexions")
        
        with col2:
            # Distribution des distances
            distances = [c.get('distance', 0) for c in visible_connections]
            if distances:
                avg_distance = sum(distances) / len(distances)
                max_distance = max(distances)
                min_distance = min(distances)
                
                st.write("**Distances FTL:**")
                st.write(f"• Moyenne: {avg_distance:.1f} UA")
                st.write(f"• Maximum: {max_distance} UA")
                st.write(f"• Minimum: {min_distance} UA")

def main():
    """Interface principale de la page réseau FTL"""
    st.title("🌌 Réseau FTL - Visualisation interactive")
    st.markdown("Exploration graphique des connexions de transport FTL entre les systèmes stellaires")
    
    # Charger les données
    data = load_ftl_data()
    if not data:
        st.stop()
    
    # Contrôles
    st.sidebar.title("⚙️ Configuration")
    
    # Toggle pour les liens privés
    show_private = st.sidebar.checkbox(
        "🔒 Afficher les liens privés", 
        value=True,
        help="Les liens privés sont représentés en rouge et en pointillés"
    )
    
    # Contrôle de la taille des nœuds
    node_size = st.sidebar.slider(
        "� Taille des systèmes",
        min_value=5,
        max_value=50,
        value=15,
        help="Ajuster la taille des nœuds représentant les systèmes stellaires"
    )
    
    # Filtre par distance
    if data and data.get('connections'):
        distances = [c.get('distance', 5) for c in data['connections']]
        if distances:
            max_dist = max(distances)
            min_dist = min(distances)
            
            distance_filter = st.sidebar.slider(
                "🚀 Distance maximale FTL",
                min_value=min_dist,
                max_value=max_dist,
                value=max_dist,
                help="Filtrer les connexions par distance maximale"
            )
    
    # Afficher les statistiques
    if 'distance_filter' in locals():
        show_network_stats(data, show_private, distance_filter)
    else:
        show_network_stats(data, show_private)
    
    st.markdown("---")
    
    # Légende
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🎨 Légende:**")
        st.markdown("🔵 **Systèmes stellaires** - Taille proportionnelle aux connexions")
        st.markdown("📏 **Longueur des liens** - Proportionnelle à la distance FTL")
    with col2:
        st.markdown("🟢 **Liens répertoriés** - Connexions publiques connues")
        if show_private:
            st.markdown("🔴 **Liens privés** - Connexions secrètes ou non officielles")
        st.markdown("🎯 **Largeur des liens** - Inversement proportionnelle à la distance")
    
    # Affichage du graphique
    st.subheader("🗺️ Carte du réseau FTL")
    
    # Graphique Agraph interactif
    if 'distance_filter' in locals():
        nodes, edges = create_network_graph(data, show_private, distance_filter, node_size)
    else:
        nodes, edges = create_network_graph(data, show_private, None, node_size)
    
    config = Config(
        width=1000,
        height=700,
        directed=False,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False,
        # Configuration de physique pour respecter les distances
        physics_config={
            "enabled": True,
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.3,
                "springLength": 95,
                "springConstant": 0.04,
                "damping": 0.09
            },
            "maxVelocity": 50,
            "minVelocity": 0.1,
            "solver": "barnesHut",
            "stabilization": {"iterations": 150}
        }
    )
    
    if nodes and edges:
        agraph(nodes=nodes, edges=edges, config=config)
    else:
        st.warning("⚠️ Aucune donnée à afficher avec les paramètres actuels")
    
    # Informations techniques
    with st.expander("ℹ️ Informations techniques"):
        st.markdown(f"""
        **Source des données:** `univers_eneria_reseau_ftl.json`
        
        **Moteur de rendu:** Streamlit-Agraph (interactif)
        
        **Couleurs:**
        - 🔵 Systèmes: Bleu (#4A90E2)
        - 🟢 Liens répertoriés: Vert (#51CF66) 
        - 🔴 Liens privés: Rouge (#FF6B6B)
        
        **Proportionnalité:**
        - **Taille des nœuds:** Base réglable + bonus connexions (×2)
        - **Longueur des arêtes:** Distance FTL (×20 pour physique)
        - **Largeur des arêtes:** Inversement proportionnelle à la distance (6-distance)
        
        **Physique:** BarnesHut avec springs ajustés pour respecter les distances FTL
        """)
        
        st.markdown("**Contrôles:**")
        st.markdown("- 🖱️ **Drag:** Déplacer les nœuds")
        st.markdown("- 🔍 **Zoom:** Molette de la souris")
        st.markdown("- 📏 **Taille:** Slider dans la barre latérale")
        st.markdown("- 🔒 **Liens privés:** Toggle dans la barre latérale")
        
        if 'distance_filter' in locals():
            st.markdown(f"**Filtre actuel:** Distance FTL ≤ {distance_filter} UA")

if __name__ == "__main__":
    main()
