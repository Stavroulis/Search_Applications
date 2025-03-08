import streamlit as st
import json
from pathlib import Path

# Ensure filename is in session state BEFORE using it
if "filename" not in st.session_state:
    st.warning("No file selected. Please go to the main page.")
    st.stop()

filename = st.session_state["filename"]          
directory = Path(f"data/{filename}")
directory.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
file_path = directory / f"Summary_{filename}.json"

st.title(f"Download the summary  {filename}")

# Load the JSON file
try:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        cl_1_list = data.get("Feature Table", {}).get("Cl_1", [])
except (FileNotFoundError, json.JSONDecodeError) as e:
    st.error(f"Error loading file: {e}")
    st.stop()

# Show the download button
if file_path.exists():
    with open(file_path, "rb") as f:
        st.download_button(
            label="📥 DOWNLOAD JSON FILE",
            data=f,
            file_name=f"Summary_{filename}.json",
            mime="application/json"
        )
else:
    st.warning("No file available for download.")
