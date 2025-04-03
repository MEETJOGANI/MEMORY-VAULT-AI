import streamlit as st
import networkx as nx
import plotly.graph_objects as go
from collections import defaultdict
import random

def generate_mind_map(memories, max_connections=50):
    """
    Generate an interactive mind map visualization of memory connections.
    
    Args:
        memories (list): List of memory objects to visualize
        max_connections (int): Maximum number of connections to display for visual clarity
        
    Returns:
        plotly.graph_objects.Figure: Interactive mind map figure
    """
    # Create a graph
    G = nx.Graph()
    
    # Add nodes (memories)
    for memory in memories:
        memory_id = memory.get('id')
        # Add a node for each memory
        G.add_node(memory_id, 
                  label=memory.get('text')[:50] + '...' if len(memory.get('text')) > 50 else memory.get('text'),
                  date=memory.get('date')[:10],
                  emotion=memory.get('emotion', 'Unknown'),
                  type='memory')
    
    # Create connections based on shared properties
    connections = []
    
    # Connect memories with similar topics
    topic_memories = defaultdict(list)
    for memory in memories:
        for topic in memory.get('topics', []):
            topic_memories[topic].append(memory.get('id'))
    
    for topic, mem_ids in topic_memories.items():
        if len(mem_ids) > 1:
            for i in range(len(mem_ids)):
                for j in range(i+1, len(mem_ids)):
                    connections.append((mem_ids[i], mem_ids[j], 'topic', topic))
    
    # Connect memories with shared people
    people_memories = defaultdict(list)
    for memory in memories:
        for person in memory.get('people', []):
            people_memories[person].append(memory.get('id'))
    
    for person, mem_ids in people_memories.items():
        if len(mem_ids) > 1:
            for i in range(len(mem_ids)):
                for j in range(i+1, len(mem_ids)):
                    connections.append((mem_ids[i], mem_ids[j], 'person', person))
    
    # Connect memories with same emotion
    emotion_memories = defaultdict(list)
    for memory in memories:
        emotion = memory.get('emotion', 'Unknown')
        emotion_memories[emotion].append(memory.get('id'))
    
    for emotion, mem_ids in emotion_memories.items():
        if len(mem_ids) > 1:
            # Limit connections per emotion to avoid overcrowding
            sample_size = min(10, len(mem_ids))
            sample_ids = random.sample(mem_ids, sample_size)
            for i in range(len(sample_ids)):
                for j in range(i+1, len(sample_ids)):
                    connections.append((sample_ids[i], sample_ids[j], 'emotion', emotion))
    
    # Connect memories with same location
    location_memories = defaultdict(list)
    for memory in memories:
        location = memory.get('location')
        if location and location != 'Unknown':
            location_memories[location].append(memory.get('id'))
    
    for location, mem_ids in location_memories.items():
        if len(mem_ids) > 1:
            for i in range(len(mem_ids)):
                for j in range(i+1, len(mem_ids)):
                    connections.append((mem_ids[i], mem_ids[j], 'location', location))
    
    # Limit the number of connections to avoid visual overload
    if len(connections) > max_connections:
        connections = random.sample(connections, max_connections)
    
    # Add edges with attributes
    for source, target, conn_type, conn_label in connections:
        G.add_edge(source, target, type=conn_type, label=conn_label)
    
    # Use a force-directed layout algorithm
    pos = nx.spring_layout(G, seed=42)
    
    # Create a Plotly figure
    edge_traces = []
    
    # Define colors for different connection types
    color_map = {
        'topic': 'rgba(65, 105, 225, 0.7)',    # Blue
        'person': 'rgba(255, 165, 0, 0.7)',    # Orange
        'emotion': 'rgba(50, 205, 50, 0.7)',   # Green
        'location': 'rgba(147, 112, 219, 0.7)' # Purple
    }
    
    # Create traces for edges by type
    for edge_type in color_map.keys():
        edge_x = []
        edge_y = []
        edge_text = []
        
        for edge in G.edges(data=True):
            if edge[2].get('type') == edge_type:
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                edge_text.append(edge[2].get('label', ''))
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1.5, color=color_map[edge_type]),
            hoverinfo='text',
            mode='lines',
            name=f'Shared {edge_type.capitalize()}',
            text=edge_text
        )
        edge_traces.append(edge_trace)
    
    # Create node trace
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []
    
    # Color map for emotions
    emotion_colors = {
        'Happy': '#55efc4',
        'Sad': '#74b9ff',
        'Angry': '#ff7675',
        'Surprised': '#a29bfe',
        'Anxious': '#ffeaa7',
        'Peaceful': '#81ecec',
        'Nostalgic': '#fab1a0',
        'Excited': '#fdcb6e',
        'Grateful': '#55efc4',
        'Confused': '#636e72',
        'Proud': '#6c5ce7',
        'Embarrassed': '#e84393',
        'Hopeful': '#00b894',
        'Neutral': '#dfe6e9'
    }
    
    # Default color for unknown emotions
    default_color = '#dfe6e9'
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        # Node text for hover info
        node_info = G.nodes[node]
        text = f"Date: {node_info.get('date')}<br>"
        text += f"Memory: {node_info.get('label')}<br>"
        text += f"Emotion: {node_info.get('emotion')}"
        node_text.append(text)
        
        # Node size based on connections - use a simpler approach
        connections = 0
        # Count direct edges to this node
        for edge in G.edges():
            if node in edge:
                connections += 1
                
        # Use connections count for node size
        degree_value = connections
            
        size = 15 + degree_value * 2  # Base size + bonus for connections
        node_size.append(size)
        
        # Node color based on emotion
        emotion = G.nodes[node].get('emotion', 'Unknown')
        node_color.append(emotion_colors.get(emotion, default_color))
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color=node_color,
            size=node_size,
            line=dict(width=2, color='white')
        ),
        text=node_text,
        name='Memories'
    )
    
    # Create figure
    fig = go.Figure(data=edge_traces + [node_trace])
    
    # Add layout configuration separately
    fig.update_layout(
        title='Memory Mind Map',
        showlegend=True,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        annotations=[ dict(
            text="Hover over nodes to see memory details",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.005, y=-0.002
        )],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(248,248,248,1)',
        paper_bgcolor='rgba(248,248,248,1)',
        legend=dict(
            x=1.05,
            y=0.5,
            traceorder='normal',
            font=dict(
                family='sans-serif',
                size=12,
                color='#000'
            ),
            bgcolor='#fff',
            bordercolor='#ddd',
            borderwidth=1
        )
    )
    
    # Update layout for better interactivity
    fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        ),
        title_font_size=24
    )
    
    return fig
