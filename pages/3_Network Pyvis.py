import streamlit as st
import json
import networkx as nx
from pathlib import Path
import pandas as pd
from pyvis.network import Network
import tempfile
from itertools import cycle
from rapidfuzz import process  # Fast fuzzy matching

# Constants
COLORS = ["red", "orange", "lime", "turquoise", "hotpink", "khaki", "blue", "green", "yellow", "violet", "coral", "pink", "steelblue", "salmon", "tomato", "springgreen"] * 10

# Helper functions for graph-related operations
def load_existing_data(filename):
    directory = Path(f"data/{filename}")
    directory.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    file_path = directory / f"Summary_{filename}.json"
    
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f), file_path
    return {}, file_path

def find_best_match(target, candidates):
    if not candidates:
        return None
    
    match, score, _ = process.extractOne(target, candidates)  # Get best match & similarity score
    return match if score > 60 else None  # Set a threshold to avoid weak matches

def create_graph_new(df):
    G = nx.DiGraph()
    
    color_cycle = cycle([
        "red", "orange", "lime", "turquoise", "hotpink", "khaki", "blue", 
        "green", "yellow", "violet", "coral", "pink", "steelblue", "salmon", 
        "tomato", "springgreen"
    ])
    
    # Assign colors based on first appearance in 'a_list'
    node_colors = {}
    claim_colors = {}
    
    for idx, row in df.iterrows():
        node = row['a_list']
        claim = row['Cl_nr']
        
        if pd.notna(node) and node.strip():
            if node not in node_colors:
                if claim not in claim_colors:
                    claim_colors[claim] = next(color_cycle)
                node_colors[node] = claim_colors[claim]
    
    # Add nodes with their assigned colors
    for node, color in node_colors.items():
        G.add_node(node, color=color)
    
    # Add edges based on new logic
    for i in range(len(df) - 2):
        node_a = None
        node_b = None
        edge_label = df.at[i + 1, 'prep_list'] if pd.notna(df.at[i + 1, 'prep_list']) else ""
        
        # Condition (a): 'a_list[i]' is a string, 'the_list[i+2]' is empty, 'a_list[i+2]' is a string
        if pd.notna(df.at[i, 'a_list']) and df.at[i, 'a_list'].strip():
            if pd.isna(df.at[i + 2, 'the_list']) or not df.at[i + 2, 'the_list'].strip():
                if pd.notna(df.at[i + 2, 'a_list']) and df.at[i + 2, 'a_list'].strip():
                    node_a = df.at[i, 'a_list']
                    node_b = df.at[i + 2, 'a_list']
        
        # Condition (b): 'the_list[i]' is a string, 'a_list[i+2]' is a string
        elif pd.notna(df.at[i, 'the_list']) and df.at[i, 'the_list'].strip():
            if pd.notna(df.at[i + 2, 'a_list']) and df.at[i + 2, 'a_list'].strip():
                node_a = next((n for n in df['a_list'] if n == df.at[i, 'the_list']), None)
                node_b = df.at[i + 2, 'a_list']
        
        if node_a and node_b:
            G.add_edge(node_a, node_b, label=edge_label)
    
    return G

def create_graph(df):
    G = nx.DiGraph()
    
    color_cycle = cycle([
        "red", "orange", "lime", "turquoise", "hotpink", "khaki", "blue", 
        "green", "yellow", "violet", "coral", "pink", "steelblue", "salmon", 
        "tomato", "springgreen"
    ])
    
    # Assign colors based on first appearance in 'a_list'
    node_colors = {}
    claim_colors = {}
    
    for idx, row in df.iterrows():
        node = row['a_list']
        claim = row['Cl_nr']
        
        if pd.notna(node) and node.strip():
            if node not in node_colors:
                if claim not in claim_colors:
                    claim_colors[claim] = next(color_cycle)
                node_colors[node] = claim_colors[claim]

    # Add nodes with their assigned colors
    for node, color in node_colors.items():
        G.add_node(node, color=color)
    
    # Add edges based on both old and new logic
    for i in range(len(df) - 2):
        node_a = None
        node_b = None
        edge_label = df.at[i + 1, 'prep_list'] if pd.notna(df.at[i + 1, 'prep_list']) else ""
        
        # Condition (a): 'a_list[i]' is a string, 'the_list[i+2]' is empty, 'a_list[i+2]' is a string
        if pd.notna(df.at[i, 'a_list']) and df.at[i, 'a_list'].strip():
            if pd.isna(df.at[i + 2, 'the_list']) or not df.at[i + 2, 'the_list'].strip():
                if pd.notna(df.at[i + 2, 'a_list']) and df.at[i + 2, 'a_list'].strip():
                    node_a = df.at[i, 'a_list']
                    node_b = df.at[i + 2, 'a_list']
        
        # Condition (b): 'the_list[i]' is a string, 'a_list[i+2]' is a string
        elif pd.notna(df.at[i, 'the_list']) and df.at[i, 'the_list'].strip():
            if pd.notna(df.at[i + 2, 'a_list']) and df.at[i + 2, 'a_list'].strip():
                node_a = next((n for n in df['a_list'] if n == df.at[i, 'the_list']), None)
                node_b = df.at[i + 2, 'a_list']
        
        if node_a and node_b:
            G.add_edge(node_a, node_b, label=edge_label)

    # Identify the first node in a_list (assuming it's the first non-empty string)
    first_node = next((node for node in df['a_list'] if pd.notna(node) and node.strip()), None)

    # Connect first node to other nodes in 'a_list' if no edge exists in 'the_list'
    if first_node:
        for node in df['a_list']:
            if node and node != first_node:
                has_edge = any(G.has_edge(node, other) for other in df['the_list'])
                if not has_edge:
                    G.add_edge(first_node, node)

    # Ensure all nodes have a subset attribute (default to 0 if missing)
    nx.set_node_attributes(G, {node: 0 for node in G.nodes}, "subset")

    return G

def display_pyvis_graph(G):
    """Create an interactive Pyvis graph ensuring each node appears only once and retains its first assigned color."""
    net = Network(notebook=False)

    for node, attrs in G.nodes(data=True):
        if isinstance(node, (str, int)):  # Ensure valid node type
            # Use the color from the node's attributes directly
            color = attrs.get("color", "lightblue")  # Default to lightblue if no color is found
            net.add_node(str(node), label=str(node), color=color)

    for edge in G.edges(data=True):
        if isinstance(edge[0], (str, int)) and isinstance(edge[1], (str, int)):
            net.add_edge(str(edge[0]), str(edge[1]), title=edge[2].get("label", ""))

    return net

def save_network(G, file_path):
    if "" in G.nodes:
        G.remove_node("")

    # Prepare network data
    network_data = {
        "nodes": [{"id": node, "color": G.nodes[node].get("color", "lightblue")} for node in G.nodes],
        "edges": [{"source": edge[0], "target": edge[1], "label": G.edges[edge].get("label", "")} for edge in G.edges],
    }

    # Ensure correct JSON structure
    data = {}
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}  # Reset if the JSON is corrupted

    data["Network"] = network_data

    # Debugging: Print JSON before saving
    print(json.dumps(data, indent=4))

    # Write updated JSON
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    st.success(f"Graph saved successfully to {file_path}")

def display_color_legend(num_claims):
    st.subheader("Claim Color Legend")
    for i in range(num_claims):
        st.markdown(
            f'<span style="color: {COLORS[i]}; font-weight: bold;">■ Claim {i+1}</span>',
            unsafe_allow_html=True
        )

def display_graph_controls(G):
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Modify Graph")
    st.markdown("<br>", unsafe_allow_html=True)

    # Add Node & Delete Node
    col1, col2 = st.columns([3, 1])
    with col1:
        with st.form("add_node_form"):
            new_node = st.text_input("Node Name")
            add_node_submit = st.form_submit_button("Add Node")
    with col2:
        with st.form("del_node_form"):
            node_to_delete = st.selectbox("Delete Node", list(G.nodes), key="del_node")
            del_node_submit = st.form_submit_button("Del Node")

    if add_node_submit and new_node:
        if new_node not in G.nodes:
            G.add_node(new_node, color="yellow")  # Highlight new nodes in yellow
            st.session_state["G"] = G  # Persist changes
            st.rerun()

    if del_node_submit and node_to_delete:
        G.remove_node(node_to_delete)
        st.session_state["G"] = G  # Persist changes
        st.rerun()

    # Add Edge & Delete Edge
    col3, col4 = st.columns([3, 1])
    with col3:
        with st.form("add_edge_form"):
            node_options = list(G.nodes)
            edge_node1 = st.selectbox("From", node_options, key="edge1")
            edge_node2 = st.selectbox("To", node_options, key="edge2")
            edge_label = st.text_input("Edge Label (optional)")
            add_edge_submit = st.form_submit_button("Add Edge")
    with col4:
        with st.form("del_edge_form"):
            edge_options = [f"{u} -> {v}" for u, v in G.edges]
            edge_to_delete = st.selectbox("Delete Edge", edge_options, key="del_edge")
            del_edge_submit = st.form_submit_button("Del Edge")

    if add_edge_submit and edge_node1 and edge_node2:
        G.add_edge(edge_node1, edge_node2, label=edge_label)
        st.session_state["G"] = G  # Persist changes
        st.rerun()

    if del_edge_submit and edge_to_delete:
        u, v = edge_to_delete.split(" -> ")
        G.remove_edge(u, v)
        st.session_state["G"] = G  # Persist changes
        st.rerun()

def concatatened_dataframe(data):
    rows = []

    # Iterate through each claim in the "data" dictionary
    for claim_key, claim_data in data.items():
        a_list = data['a_list']
        prep_list = data['prep_list']
        the_list = data['the_list']
        cl_nr_list = data['Cl_nr']
        
        # Determine the maximum length for lists
        max_len = max(len(a_list), len(prep_list), len(the_list))
        
        # Pad the lists to make them the same length
        a_list += [''] * (max_len - len(a_list))
        prep_list += [''] * (max_len - len(prep_list))
        the_list += [''] * (max_len - len(the_list))
        cl_nr_list += [''] * (max_len - len(cl_nr_list))    
        
        # Add rows for each claim
        for i in range(max_len):
            rows.append([i, a_list[i], prep_list[i], the_list[i], cl_nr_list[i]])
    
    # Create a DataFrame
    df = pd.DataFrame(rows, columns=['index', 'a_list', 'prep_list', 'the_list', 'Cl_nr'])
    #st.dataframe(df)
    return df

def main():
    
    if "filename" not in st.session_state:
        st.warning("No file selected. Please go to the main page.")
        st.stop()

    filename = st.session_state["filename"]
    data, file_path = load_existing_data(filename)
    network_features = data.get("Concatenated DataFrame", {})

    # Generate concatenated dataframe
    if isinstance(network_features, dict):
        df = concatatened_dataframe(network_features)
    else:
        st.error("Invalid data format: network_features should be a dictionary.")

    st.title(f"Network Graph for {filename}")

    # Display color legend
    display_color_legend(len(network_features))

    # Create or load graph
    if "G" not in st.session_state:
        if "Network" in data:
            # Reconstruct graph from saved JSON
            G = nx.DiGraph()
            for node in data["Network"]["nodes"]:
                G.add_node(node["id"], color=node.get("color", "lightblue"))
            for edge in data["Network"]["edges"]:
                G.add_edge(edge["source"], edge["target"], label=edge.get("label", ""))
            st.session_state["G"] = G
        else:
            G = create_graph(df)
            st.session_state["G"] = G
    else:
        G = st.session_state["G"]

    # Display the network graph
    net = display_pyvis_graph(G)
    temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".html").name
    net.save_graph(temp_path)
    st.components.v1.html(open(temp_path, "r", encoding="utf-8").read(), height=500)

    # Graph modification UI
    display_graph_controls(G)

    # Save Network Button
    if st.button("Save", type="primary", use_container_width=True):
        save_network(G, file_path)
        st.session_state["graph_saved"] = True

if __name__ == "__main__":
    main()
