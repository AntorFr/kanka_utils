"""
Page de visualisation du réseau FTL
Interface Streamlit pour afficher graphiquement les connexions FTL entre systèmes
"""

import streamlit as st
import json
import os
from streamlit_agraph import agraph, Node, Edge, Config
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
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

def create_network_graph(data: Dict, show_private: bool = True, max_distance: int = None) -> Tuple[List[Node], List[Edge]]:
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
        # Taille du nœud proportionnelle au nombre de connexions
        size = min(30 + system_data.get('connections_count', 0) * 3, 60)
        
        node = Node(
            id=system_name,
            label=system_name,
            size=size,
            color="#4A90E2",  # Bleu pour tous les systèmes
            font={"size": 14, "color": "#FFFFFF"},
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
        
        # Largeur proportionnelle à la distance (inversée)
        distance = conn.get('distance', 5)
        width = max(1, 6 - distance)
        
        edge = Edge(
            source=conn['source'],
            target=conn['target'],
            color=color,
            width=width,
            dashes=dashes,
            label=f"Distance: {distance}",
            font={"size": 10}
        )
        edges.append(edge)
        edge_id += 1
    
    return nodes, edges

def create_plotly_network(data: Dict, show_private: bool = True, layout_type: str = "spring", max_distance: int = None):
    """
    Crée un graphique réseau avec Plotly
    """
    # Créer un graphe NetworkX
    G = nx.Graph()
    
    # Ajouter les nœuds
    systems = data.get('systems', {})
    for system_name, system_data in systems.items():
        G.add_node(system_name, connections=system_data.get('connections_count', 0))
    
    # Ajouter les arêtes avec filtrage
    connections = data.get('connections', [])
    public_edges = []
    private_edges = []
    
    for conn in connections:
        is_private = conn.get('prive', False) or conn.get('status', '').lower().find('privée') >= 0
        if is_private and not show_private:
            continue
        
        # Filtrer par distance si spécifié
        distance = conn.get('distance', 5)
        if max_distance and distance > max_distance:
            continue
            
        G.add_edge(conn['source'], conn['target'], 
                  distance=distance,
                  private=is_private)
        
        if is_private:
            private_edges.append((conn['source'], conn['target']))
        else:
            public_edges.append((conn['source'], conn['target']))
    
    # Calculer les positions avec différents layouts
    if layout_type == "spring (Force-directed)":
        pos = nx.spring_layout(G, k=3, iterations=50)
    elif layout_type == "circular":
        pos = nx.circular_layout(G)
    elif layout_type == "kamada_kawai":
        pos = nx.kamada_kawai_layout(G)
    elif layout_type == "random":
        pos = nx.random_layout(G)
    else:
        pos = nx.spring_layout(G, k=3, iterations=50)
    
    # Préparer les données pour Plotly
    edge_x_public = []
    edge_y_public = []
    edge_x_private = []
    edge_y_private = []
    
    # Arêtes publiques
    for edge in public_edges:
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x_public.extend([x0, x1, None])
        edge_y_public.extend([y0, y1, None])
    
    # Arêtes privées
    for edge in private_edges:
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x_private.extend([x0, x1, None])
        edge_y_private.extend([y0, y1, None])
    
    # Nœuds
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        connections = G.nodes[node].get('connections', 0)
        node_text.append(f"{node}<br>Connexions: {connections}")
        node_size.append(max(20, connections * 4))
    
    # Créer le graphique
    fig = go.Figure()
    
    # Ajouter les arêtes publiques
    if edge_x_public:
        fig.add_trace(go.Scatter(
            x=edge_x_public, y=edge_y_public,
            mode='lines',
            line=dict(width=2, color='#51CF66'),
            hoverinfo='none',
            showlegend=True,
            name="Liens répertoriés"
        ))
    
    # Ajouter les arêtes privées
    if edge_x_private:
        fig.add_trace(go.Scatter(
            x=edge_x_private, y=edge_y_private,
            mode='lines',
            line=dict(width=2, color='#FF6B6B', dash='dash'),
            hoverinfo='none',
            showlegend=True,
            name="Liens privés"
        ))
    
    # Ajouter les nœuds
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        marker=dict(
            size=node_size,
            color='#4A90E2',
            line=dict(width=2, color='white')
        ),
        text=[node for node in G.nodes()],
        textposition="middle center",
        textfont=dict(color="white", size=10),
        hoverinfo='text',
        hovertext=node_text,
        showlegend=True,
        name="Systèmes stellaires"
    ))
    
    fig.update_layout(
        title="Réseau FTL - Univers d'Eneria",
        showlegend=True,
        hovermode='closest',
        margin=dict(b=20,l=5,r=5,t=40),
        annotations=[ dict(
            text="Réseau de transport FTL entre les systèmes stellaires",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.005, y=-0.002,
            xanchor='left', yanchor='bottom',
            font=dict(color="#888", size=12)
        )],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

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
    
    # Type de visualisation
    viz_type = st.sidebar.selectbox(
        "📊 Type de visualisation",
        ["Plotly (Recommandé)", "Agraph (Interactif)"],
        help="Plotly offre de meilleures performances pour les gros réseaux"
    )
    
    # Options de layout
    if viz_type == "Plotly (Recommandé)":
        layout_type = st.sidebar.selectbox(
            "🎯 Layout du graphique",
            ["spring (Force-directed)", "circular", "kamada_kawai", "random"],
            help="Différents algorithmes de positionnement des nœuds"
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
    with col2:
        st.markdown("🟢 **Liens répertoriés** - Connexions publiques connues")
        if show_private:
            st.markdown("🔴 **Liens privés** - Connexions secrètes ou non officielles")
    
    # Affichage du graphique
    st.subheader("🗺️ Carte du réseau")
    
    if viz_type == "Plotly (Recommandé)":
        # Graphique Plotly
        if 'distance_filter' in locals():
            fig = create_plotly_network(data, show_private, layout_type, distance_filter)
        else:
            fig = create_plotly_network(data, show_private, layout_type)
        st.plotly_chart(fig, use_container_width=True, height=600)
        
    else:
        # Graphique Agraph (plus interactif mais plus lourd)
        if 'distance_filter' in locals():
            nodes, edges = create_network_graph(data, show_private, distance_filter)
        else:
            nodes, edges = create_network_graph(data, show_private)
        
        config = Config(
            width=800,
            height=600,
            directed=False,
            physics=True,
            hierarchical=False,
            nodeHighlightBehavior=True,
            highlightColor="#F7A7A6",
            collapsible=False
        )
        
        if nodes and edges:
            agraph(nodes=nodes, edges=edges, config=config)
        else:
            st.warning("⚠️ Aucune donnée à afficher avec les paramètres actuels")
    
    # Informations techniques
    with st.expander("ℹ️ Informations techniques"):
        st.markdown(f"""
        **Source des données:** `univers_eneria_reseau_ftl.json`
        
        **Algorithme de positionnement:** Spring Layout (Force-directed)
        
        **Couleurs:**
        - 🔵 Systèmes: Bleu (#4A90E2)
        - 🟢 Liens répertoriés: Vert (#51CF66) 
        - 🔴 Liens privés: Rouge (#FF6B6B)
        
        **Taille des nœuds:** Proportionnelle au nombre de connexions (20-60px)
        
        **Largeur des arêtes:** Inversement proportionnelle à la distance FTL
        """)

if __name__ == "__main__":
    main()
