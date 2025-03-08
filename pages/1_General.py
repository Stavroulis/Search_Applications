import streamlit as st
import json
from pathlib import Path
from PIL import Image
from datetime import datetime

# Configure Streamlit
st.set_page_config(layout="wide")

# Ensure filename is in session state
if "filename" not in st.session_state:
    st.warning("No file selected. Please go to the main page.")
    st.stop()

filename = st.session_state["filename"]
st.title(f"General Information for {filename}")

# Define paths
directory = Path(f"data/{filename}")
directory.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
file_path = directory / f"Summary_{filename}.json"

# Load existing data
if file_path.exists():
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {}

# Initialize session state for general data
st.session_state.setdefault("gen_data", data)

# Define input placeholders
PLACEHOLDERS = {
    "Independent Claims": "Claim 1 discloses ...",
    "Ptbs": "How to improve, prevent, enable...",
    "Technical Effect": "Reduce non-linearity, increase sensitivity/accuracy, reduce effort...",
    "Solution": "By...",
    "Keywords": "Enter relevant keywords...",
    "Classes": "Enter classification info...",
    "Unity": "Describe unity...",
    "Remarks": "Consulted: ...",
    "Prior Art": "Enter prior art information..."
}

# Create layout
col_general, col_claims, col_image = st.columns([0.3, 0.3, 0.3])

# General Information Inputs
with col_general:
    st.subheader("General")
    for key, placeholder in PLACEHOLDERS.items():
        st.session_state["gen_data"][key] = st.text_area(
            key,
            value=st.session_state["gen_data"].get(key, ""),
            key=f"input_{key}",
            placeholder=placeholder
        )

# Claims Input
with col_claims:
    st.subheader("Claims")
    st.session_state["gen_data"]["Nr. Claims"] = st.text_input(
        "Number of claims",
        value=st.session_state["gen_data"].get("Nr. Claims", ""),
        key="nr_claims",
        placeholder="Enter number of claims..."
    )

# Image Upload & Display
with col_image:
    st.subheader("Appl. Image")
    uploaded_image = st.file_uploader("Upload an Image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
    image_path = directory / f"appl_image_{filename}.png"

    if uploaded_image:
        with open(image_path, "wb") as img_file:
            img_file.write(uploaded_image.getbuffer())
        st.session_state["gen_data"]["Appl. Image"] = str(image_path)
        st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)
    elif "Appl. Image" in st.session_state["gen_data"]:
        try:
            image = Image.open(st.session_state["gen_data"]["Appl. Image"])
            st.image(image, caption="Application Image", use_container_width=True)
        except Exception as e:
            st.error(f"Error loading image: {e}")

# Save Data Function
if st.button("Save", type="primary", use_container_width=True):
    st.session_state["gen_data"]["Date"] = datetime.now().strftime("%d-%m-%Y")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(st.session_state["gen_data"], f, indent=4)
    st.success(f"Data successfully saved to {file_path}")
