import streamlit as st
import json
import networkx as nx
import numpy as np
from pathlib import Path

# Load the English NLP model
import spacy
nlp = spacy.load("en_core_web_sm")

# Define the path for the file storage
def get_file_path(filename: str) -> Path:
    directory = Path(f"data/{filename}")
    directory.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
    return directory / f"Summary_{filename}.json"

# Load data from the JSON file
def load_network_data(file_path: Path):
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("Network", {}), data
    return {}, {}

# Create the network graph from the given network data
def create_graph_from_network_data(network_data):
    G = nx.DiGraph()
    
    # Add nodes with their colors as node attributes
    for node in network_data.get('nodes', []):
        G.add_node(node['id'], color=node['color'])
    
    # Add edges between nodes
    for edge in network_data.get('edges', []):
        G.add_edge(edge['source'], edge['target'], label=edge.get('label', ''))
    
    return G

# Extract head nodes (nodes with no incoming edges)
def find_head_nodes(G):
    return [node for node in G.nodes if G.in_degree(node) == 0]

# Find all branches starting from a specific node and filter out branches of length <= 1
def find_all_branches(G, start_node):
    branches = []
    
    def dfs(current_path):
        current_node = current_path[-1]
        # Explore all neighbors (children in a directed graph)
        for neighbor in G.neighbors(current_node):
            if neighbor not in current_path:  # Avoid cycles
                dfs(current_path + [neighbor])
        # If no neighbors, the branch is complete, only add it if length > 1
        if len(current_path) > 1:
            branches.append(current_path)
    
    dfs([start_node])
    return branches

# Generate a dictionary for the "Markers" field
def generate_markers_dict(network_data, G):
    head_nodes = find_head_nodes(G)
    
    # Find all branches, but only include those with more than 1 element in the branch
    all_branches = {head_node: find_all_branches(G, head_node) for head_node in head_nodes}

    # Generate "Combinations" (list of node IDs)
    combinations = [node['id'] for node in network_data.get("nodes", [])]

    # Format the branches for display, filtering out those with one or fewer elements
    branches_info = {
        head_node: [
            f"10UG ({', '.join(branch)})" for branch in branches if len(branch) > 1  # Only keep branches with length > 1
        ]
        for head_node, branches in all_branches.items() if any(len(branch) > 1 for branch in branches)  # Only include head nodes with valid branches
    }

    # Construct the dictionary to return
    markers_dict = {
        "Combinations": combinations,
        "Heads": head_nodes,
        "Branches": branches_info
    }

    return markers_dict

# Format the markers dictionary as text for the text area
def format_markers_for_display(markers_dict):
    formatted_text = ""

    # Format each section with the appropriate titles and values
    for key, value in markers_dict.items():
        formatted_text += f"{key}\n\n"  # Key as title
        if isinstance(value, list):
            formatted_text += "\n".join(value) + "\n"  # Each combination on a new line
        elif isinstance(value, dict):
            for head_node, branches in value.items():
                formatted_text += f"{head_node}:\n"  # Display head node on a new line
                formatted_text += "\n".join(branches) + "\n"  # Each branch on a new line
        formatted_text += "\n---   ---   ---   --- \n\n"  # Separator between sections

    return formatted_text.strip()  # Remove the last empty line after the last separator

# Streamlit UI - Show concepts and save changes
def display_and_save_concepts(filename: str, markers_dict: dict, existing_data: dict):
    st.title(f"Concepts aid {filename}")
    
    # Format the markers dictionary for display in the text area
    formatted_text = format_markers_for_display(markers_dict)
    
    # Display the concepts in a text area (formatted text for user)
    concepts_text = st.text_area(label="Concepts", value=formatted_text, height=500, key="concepts_text")
    
    # Save Button: Save the concepts text to JSON file, without overwriting existing data
    if st.button("Save", type="primary", use_container_width=True):
        # Update the "Markers" field in the existing data with the new markers dictionary
        existing_data["Markers"] = markers_dict  # Update the "Markers" field with the new dictionary
        
        # Save the updated data back to the file
        file_path = get_file_path(filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=4)
        
        st.success("Changes saved successfully!")

# Main Streamlit application flow
def main():
    if "filename" not in st.session_state:
        st.warning("No file selected. Please go to the main page.")
        st.stop()

    filename = st.session_state["filename"]
    file_path = get_file_path(filename)
    
    # Load network data from file, including previous data
    network_data, existing_data = load_network_data(file_path)
    
    if network_data:
        G = create_graph_from_network_data(network_data)
        markers_dict = generate_markers_dict(network_data, G)
    else:
        markers_dict = {"Combinations": [], "Heads": [], "Branches": {}}

    # Display and allow saving concepts text
    display_and_save_concepts(filename, markers_dict, existing_data)

# Run the main function
if __name__ == "__main__":
    main()
