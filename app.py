import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="Patent Analysis Tool", layout="wide")

# Custom CSS for right-aligned italic text (quote)
st.sidebar.markdown(
    """
    <style>
        .quote-container {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            height: 10vh;
            margin-top: 50px;
            margin-right: 20px;
        }
        .quote-box {
            text-align: right;
            font-style: italic;
            font-size: 18px;
            color: gray;
            max-width: 300px;
        }
        .quote-author {
            font-weight: bold;
            font-size: 16px;
            margin-top: 5px;
        }
    </style>
    <div class="quote-container">
        <div class="quote-box">
            "For understanding an application one has to read it at least once, completely"
            <div class="quote-author">— St. Stavroulis —</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
    
st.title("Patent Analysis Tool")

# File Selection
filename = st.text_input("Enter file name:")
filename = filename.upper()                             # Ensure uppercase input

if filename:
    st.session_state["filename"] = filename  # Store in session state 
    directory = Path(f"data/{filename}")
    directory.mkdir(parents=True, exist_ok=True)

    file_path = directory / f"Summary_{filename}.json"

    if file_path.exists():
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
        data = {}
        with open(file_path, "w") as f:
            json.dump(data, f)

    st.success(f"Loaded file: {file_path}")

    # Redirect to General page
    st.switch_page("pages/1_General.py")

else:
    st.warning("Please enter a file name.")

