import streamlit as st
import mini3di
from Bio.PDB import PDBParser
import tempfile
import os
import requests
import gzip
from pathlib import Path

st.set_page_config(page_title="3Di Predictor", layout="wide")
st.title("3Di Sequence Predictor")
st.write("Enter a PDB ID or upload a PDB file to predict its 3Di sequence")

def download_pdb(pdb_id):
    """Download PDB file from RCSB"""
    pdb_id = pdb_id.lower()
    
    # Try downloading from RCSB's HTTP server
    urls = [
        f"https://files.rcsb.org/download/{pdb_id}.pdb",  # Try uncompressed first
        f"https://files.rcsb.org/download/{pdb_id}.pdb.gz"  # Try compressed version
    ]
    
    for url in urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Check if the content is gzipped
                if url.endswith('.gz'):
                    return gzip.decompress(response.content)
                return response.content
        except Exception as e:
            continue
    
    return None

def predict_3di(pdb_content):
    """Predict 3Di sequence from PDB content"""
    encoder = mini3di.Encoder()
    parser = PDBParser(QUIET=True)
    
    # Save content temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdb') as tmp_file:
        if isinstance(pdb_content, str):
            tmp_file.write(pdb_content.encode())
        else:
            tmp_file.write(pdb_content)
        tmp_path = tmp_file.name
    
    try:
        struct = parser.get_structure("structure", tmp_path)
        results = []
        
        for chain in struct.get_chains():
            states = encoder.encode_chain(chain)
            sequence = encoder.build_sequence(states)
            results.append({
                'chain_id': chain.get_id(),
                'sequence': sequence
            })
        
        os.unlink(tmp_path)  # Clean up temp file
        return results
    except Exception as e:
        os.unlink(tmp_path)  # Clean up temp file
        st.error(f"Error: {str(e)}")
        return None

# Create two columns for input options
col1, col2 = st.columns(2)

with col1:
    st.subheader("Option 1: Enter PDB ID")
    pdb_id = st.text_input("Enter PDB ID (e.g., 1abc)").strip().lower()
    predict_from_id = st.button("Predict from PDB ID")

with col2:
    st.subheader("Option 2: Upload PDB File")
    uploaded_file = st.file_uploader("Choose a PDB file", type='pdb')
    
# Handle PDB ID input
if predict_from_id and pdb_id:
    if len(pdb_id) != 4:
        st.error("Please enter a valid 4-character PDB ID")
    else:
        with st.spinner(f'Downloading PDB {pdb_id} and processing...'):
            pdb_content = download_pdb(pdb_id)
            if pdb_content:
                results = predict_3di(pdb_content)
                if results:
                    st.success(f"Prediction completed for PDB ID: {pdb_id}!")
                    for result in results:
                        with st.expander(f"Chain {result['chain_id']}"):
                            st.code(result['sequence'])
                            st.download_button(
                                label=f"Download Chain {result['chain_id']} sequence",
                                data=result['sequence'],
                                file_name=f"{pdb_id}_chain_{result['chain_id']}_3di.txt"
                            )
            else:
                st.error(f"Could not download PDB ID: {pdb_id}. Please check if the PDB ID is correct.")

# Handle file upload
elif uploaded_file is not None:
    with st.spinner('Processing uploaded file...'):
        results = predict_3di(uploaded_file.getvalue())
        
    if results:
        st.success("Prediction completed for uploaded file!")
        for result in results:
            with st.expander(f"Chain {result['chain_id']}"):
                st.code(result['sequence'])
                st.download_button(
                    label=f"Download Chain {result['chain_id']} sequence",
                    data=result['sequence'],
                    file_name=f"chain_{result['chain_id']}_3di.txt"
                )
