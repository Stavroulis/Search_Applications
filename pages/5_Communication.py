import streamlit as st
import json
from pathlib import Path
import re

# Ensure filename is in session state BEFORE using it
if "filename" not in st.session_state:
    st.warning("No file selected. Please go to the main page.")
    st.stop()

filename = st.session_state["filename"]          
directory = Path(f"data/{filename}")
directory.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
file_path = directory / f"Summary_{filename}.json"

st.title(f"Citations {filename}")

# Load the JSON file and extract relevant data
try:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
        # Extract Cl_1 from User Entered Claims
        comm_text = data.get("User Entered Claims", {}).get("Cl_1", "")

        # Extract Cl_1 list from Feature Table
        cl_1_list = data.get("Edited Feature Table", {}).get("Cl_1", [])
except (FileNotFoundError, json.JSONDecodeError) as e:
    st.error(f"Error loading file: {e}")
    st.stop()

def cit_claim(comm_text):
    """
    Inserts the citation text immediately after the first appearance of each element 
    in cl_1_list without adding extra punctuation. Also ensures proper formatting.
    """
    if not cl_1_list:
        return comm_text  # If Cl_1 list is empty, return the original text

    # Create a regex pattern for matching any Cl_1 element
    pattern = r'\b(' + '|'.join(map(re.escape, cl_1_list)) + r')\b'

    def replacement(match):
        matched_text = match.group(0)
        citation = " (D1: abstr., fig., page )"

        # Get the character immediately following the match
        match_end = match.end()
        if match_end < len(comm_text) and comm_text[match_end] in ".,;:":
            return f"{matched_text}{citation}"  # Don't duplicate punctuation
        return f"{matched_text}{citation}"

    # Replace only the first occurrence of each Cl_1 term
    updated_text = re.sub(pattern, replacement, comm_text, count=0)

    # Ensure text starts with a letter
    updated_text = re.sub(r"^[^a-zA-Z]+", "", updated_text)

    # Ensure a new line after each closing bracket ")"
    updated_text = re.sub(r"\)([.,;:]?)", r")\1\n", updated_text)

    # Ensure a new line if a punctuation sign is followed by a space and "a " or "an "
    updated_text = re.sub(r"([.,;:]) (\b(?:a|an)\b )", r"\1\n\2", updated_text)

    return updated_text

# Apply citations automatically
edited_text = cit_claim(comm_text)

# Display the edited text in a single text_area (no button needed)
st.text_area("Edited Claim 1 with Citations:", value=edited_text, height=400)
