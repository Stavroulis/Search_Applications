import streamlit as st
import json
from pathlib import Path
import re
import spacy
import pandas as pd
from collections import OrderedDict

nlp = spacy.load("en_core_web_sm")

def load_claims_text(filename: str) -> str:
    data_dir = Path(f"data/{filename}")
    data_dir.mkdir(parents=True, exist_ok=True)
    file_path = data_dir / f"Summary_{filename}.json"
    
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        user_claims = data.get("User Entered Claims", {})
        if user_claims:
            return "\n\n".join(user_claims.values())
    return ""

def remove_parenthesized_text(claim: str) -> str:
    cleaned = re.sub(r'\([^)]*\)', '', claim)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def extract_noun_chunks(claim: str) -> list[str]:
    """Extracts noun chunks in their original order of appearance, removing duplicates."""
    doc = nlp(claim)
    
    chunks = [
        chunk.text for chunk in doc.noun_chunks
        if len(chunk) > 1 and all(token.is_alpha or token.is_digit or token.text in {'(', ')', ','} for token in chunk)
    ]
    
    # Use OrderedDict to remove duplicates while maintaining order of appearance
    return list(OrderedDict.fromkeys(chunks))

def apply_highlighting(claim: str, chunks: list[str]) -> str:
    highlighted_claim = claim
    for chunk in chunks:
        highlighted_claim = re.sub(rf'\b{re.escape(chunk)}\b', f'<b style="color:red;">{chunk}</b>', highlighted_claim)
    return highlighted_claim

def create_feature_table_old(features: dict, num_claims: int) -> pd.DataFrame:
    """Creates a transposed DataFrame where each claim is a column and features are rows."""
    
    # Convert dictionary to DataFrame without transposing yet
    feature_df = pd.DataFrame.from_dict(features, orient="index")
    
    # Find the maximum number of features across claims
    max_features = feature_df.shape[1]  # Number of columns before transposing
    
    # Transpose the table so that claims become columns
    feature_df = feature_df.T
    
    # Rename columns to "Cl_1, Cl_2, Cl_3, ..."
    feature_df.columns = [f"Cl_{i+1}" for i in range(num_claims)]
    
    # Ensure all rows have the correct naming: "Feature 1, Feature 2, Feature 3, ..."
    feature_df.index = [f"Feature {i+1}" for i in range(max_features)]

    return feature_df

def create_feature_table(features: dict, num_claims: int) -> pd.DataFrame:
    """Creates a transposed DataFrame where each claim is a column and features are rows,
    excluding terms that start with 'the ' or 'said '."""
    
    # Remove terms starting with "the " or "said "
    filtered_features = {
        claim: [term for term in terms if not term.lower().startswith(("the ", "said "))]
        for claim, terms in features.items()
    }
    
    # Convert dictionary to DataFrame without transposing yet
    feature_df = pd.DataFrame.from_dict(filtered_features, orient="index")
    
    # Find the maximum number of features across claims
    max_features = feature_df.shape[1] if not feature_df.empty else 0  # Number of columns before transposing
    
    # Transpose the table so that claims become columns
    feature_df = feature_df.T
    
    # Rename columns to "Cl_1, Cl_2, Cl_3, ..."
    feature_df.columns = [f"Cl_{i+1}" for i in range(num_claims)]
    
    # Ensure all rows have the correct naming: "Feature 1, Feature 2, Feature 3, ..."
    feature_df.index = [f"Feature {i+1}" for i in range(max_features)]

    return feature_df


def split_claims(claim_text, featuretable):
    """Splits claim text based on its features"""
    claim_text = re.sub(r'\s+', ' ', claim_text.strip())  

    # If no features are provided, return the entire claim_text as a single element
    if not featuretable:
        return [claim_text]

    # Create a regex pattern to match any compound noun phrase
    compound_pattern = '|'.join(map(re.escape, featuretable))

    # Split claim text using the compound noun phrases
    segments = re.split(f"({compound_pattern})", claim_text)

    # Filter out empty or whitespace-only segments
    claim_parts = [segment.strip() for segment in segments if segment.strip()]

    return claim_parts  

def clean_split_list(split_list):
    """Cleans a list of split claim elements based on the given rules."""
    if split_list:
        # Rule (a): Remove first element if it starts with a number
        if re.match(r'^\d+\.*$', split_list[0]):
            split_list.pop(0)

        # Rule (b): Remove last element if it is "." or ","
        if split_list and split_list[-1] in {".", ","}:
            split_list.pop()

        # Rule (c): Remove leading ": ", ", " if at the beginning of an element
        split_list = [re.sub(r'^[,:;]\s*', '', elem) for elem in split_list]

    return split_list

def create_dataframe_single_claim(claim_parts, featuretable):     
    a_list, the_list, prep_list = [], [], []

    for item in claim_parts:
        if item.startswith(('A ', 'a ', 'An ', 'an ')):
            a_list.append(item.split(' ', 1)[1])  
        else:
            a_list.append('')  

        if item.startswith(('The ', 'the ', 'said ')):
            the_list.append(item.split(' ', 1)[1])  
        else:
            the_list.append('')  

        if item.startswith(('A ', 'a ', 'An ', 'an ', 'The ', 'the ', 'said ')):
            prep_list.append('')
        else:
            prep_list.append(item)

    i = 0
    while i < len(prep_list):
        item = prep_list[i]
        for noun in featuretable:
            if noun in item:
                a_list.insert(i + 1, noun)
                the_list.insert(i + 1, '')
                prep_list.insert(i + 1, '')                                                 
                prep_list[i] = item.replace(noun, '').strip()                               
                i += 1                                                                      
                break
        i += 1                                                                             

    # Ensure DataFrame always has the required columns
    df = pd.DataFrame({'a_list': a_list, 'prep_list': prep_list, 'the_list': the_list})

    # Fill missing values if any
    for col in ['a_list', 'prep_list', 'the_list']:
        if col not in df.columns:
            df[col] = ""

    # Ensure DataFrame is not empty
    if df.empty:
        df = pd.DataFrame({'a_list': [""], 'prep_list': [""], 'the_list': [""]})

    df = df[df['a_list'].str.strip().astype(bool) | df['prep_list'].str.strip().astype(bool) | df['the_list'].str.strip().astype(bool)]
    df.reset_index(drop=True, inplace=True)

    return df 

def generate_concatenated_dataframe(filename: str) -> dict:
    """Generates a concatenated DataFrame from saved claims and their feature tables, including claim number."""

    file_path = Path(f"data/{filename}") / f"Summary_{filename}.json"

    if not file_path.exists():
        st.error(f"File {file_path} not found!")
        return {"a_list": [], "prep_list": [], "the_list": [], "Cl_nr": []}  # Include empty Cl_nr

    # Load saved data
    with open(file_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    original_claims = saved_data.get("User Entered Claims", {})
    feature_table = saved_data.get("Feature Table", {})

    dataframe_storage = {}  # Store DataFrames as dictionaries
    combined_df = pd.DataFrame()  # Final concatenated DataFrame

    for claim_key, claim_text in original_claims.items():
        claim_number = claim_key.split("_")[-1]  # Extract claim number
        features = feature_table.get(claim_key, [])
        split_result = split_claims(claim_text, features)
        cleaned_result = clean_split_list(split_result)

        df_claim = create_dataframe_single_claim(cleaned_result, features)

        if not df_claim.empty:
            df_claim["Cl_nr"] = claim_number  # Add claim number as a new column
            dataframe_storage[claim_key] = df_claim.to_dict(orient="list")  # Convert DataFrame to dictionary

    # Combine all DataFrames
    for claim_key, df_dict in dataframe_storage.items():
        df = pd.DataFrame(df_dict)
        if df.empty:
            continue  # Skip empty DataFrames

        combined_df = pd.concat([combined_df, df], ignore_index=True)

    # If the combined DataFrame is empty, return an empty structure
    if combined_df.empty or not {"a_list", "prep_list", "the_list", "Cl_nr"}.issubset(combined_df.columns):
        return {"a_list": [], "prep_list": [], "the_list": [], "Cl_nr": []}

    return {
        "a_list": combined_df["a_list"].tolist(),
        "prep_list": combined_df["prep_list"].tolist(),
        "the_list": combined_df["the_list"].tolist(),
        "Cl_nr": combined_df["Cl_nr"].tolist(),
    }

def save_concatenated_dataframe(file_path: Path, concatenated_data: dict) -> None:
    """Saves the concatenated data as a DataFrame under the key 'Concatenated DataFrame' in the JSON file."""
    # Convert concatenated_data into a DataFrame
    df_concat = pd.DataFrame(concatenated_data)
    
    # Convert DataFrame to dictionary (or list of lists) for JSON compatibility
    concatenated_data_dict = df_concat.to_dict(orient="list")

    # Load the existing saved data
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
    else:
        saved_data = {}

    # Add the concatenated DataFrame to the saved data under the appropriate key
    saved_data["Concatenated DataFrame"] = concatenated_data_dict

    # Save the updated data to the JSON file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(saved_data, f, indent=4, ensure_ascii=False)

def save_data(filename: str, claims: list[str], features: dict, edited_features: dict) -> None:
    """Saves claims, extracted features, and edited features to Summary_filename.json."""
    data_dir = Path(f"data/{filename}")
    data_dir.mkdir(parents=True, exist_ok=True)
    file_path = data_dir / f"Summary_{filename}.json"

    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    # Store claims and extracted features
    data["User Entered Claims"] = {f"Cl_{i+1}": claim for i, claim in enumerate(claims)}
    data["Feature Table"] = {f"Cl_{i+1}": features.get(i, []) for i in range(len(claims))}
    data["Edited Feature Table"] = {f"Cl_{i+1}": edited_features.get(f"Cl_{i+1}", []) for i in range(len(claims))}

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    st.success(f"Data saved successfully to {file_path}")

def main() -> None:
    if "filename" not in st.session_state:
        st.warning("No file selected. Please go to the main page.")
        st.stop()
    
    filename = st.session_state["filename"]
    st.title(f"Automatic Features Extraction for {filename}")

    initial_claims_text = load_claims_text(filename)
    claims_text = st.text_area(label="Claims Text", value=initial_claims_text if initial_claims_text else "", height=300, key="claims_text", placeholder="Enter your claims here and click outside the box ...")
        
    if claims_text:
        claims_list = [claim.strip() for claim in claims_text.split("\n") if claim.strip()]
        cleaned_claims = [remove_parenthesized_text(claim) for claim in claims_list]
        
        extracted_features = {i: extract_noun_chunks(claim) for i, claim in enumerate(cleaned_claims)}
        
        highlighted_claims = [apply_highlighting(claim, extracted_features[i]) for i, claim in enumerate(cleaned_claims)]
        
        formatted_claims = "".join(f'<div style="margin-bottom: 10px;">{claim}</div>' for claim in highlighted_claims)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Automatically Highlighted Claims")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(formatted_claims, unsafe_allow_html=True)

        # Create and Display the Feature Table
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Feature Table")
        st.markdown("<br>", unsafe_allow_html=True)

        feature_df = create_feature_table(extracted_features, len(cleaned_claims))
        edited_feature_df = st.data_editor(feature_df, num_rows="dynamic")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Save", type="primary", use_container_width=True):
            edited_feature_df = edited_feature_df.fillna("")
            
            edited_features_dict = {
                f"Cl_{i+1}": edited_feature_df.iloc[:, i].dropna().tolist()
                for i in range(edited_feature_df.shape[1])
            }

            # Load existing data
            file_path = Path(f"data/{filename}") / f"Summary_{filename}.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)
            else:
                saved_data = {}

            # Update and save claims/features first
            saved_data.update({
                "User Entered Claims": {f"Cl_{i+1}": claim for i, claim in enumerate(cleaned_claims)},
                "Feature Table": {f"Cl_{i+1}": extracted_features.get(i, []) for i in range(len(cleaned_claims))},
                "Edited Feature Table": edited_features_dict,
            })

            # Save updated claims and features before calling generate_concatenated_dataframe()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(saved_data, f, indent=4, ensure_ascii=False)

            # Now that the file is updated, generate the concatenated DataFrame
            concatenated_data = generate_concatenated_dataframe(filename)

            # Save the concatenated DataFrame

            save_concatenated_dataframe(file_path, concatenated_data)

            st.success(f"Data saved successfully to {file_path}")

            # Display the concatenated DataFrame
            #st.subheader("Concatenated DataFrame")
            #st.write(concatenated_data)
            #df_concat = pd.DataFrame(concatenated_data)
            #st.dataframe(df_concat)

if __name__ == "__main__":
    main()
