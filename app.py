# app.py
import streamlit as st
import mini3di
from Bio.PDB import PDBParser
import tempfile
import os

st.set_page_config(page_title="3DI Structure Predictor", layout="wide")

st.title("3DI Structure Predictor")
st.write("Upload a PDB file to predict its 3DI structure")

def predict_3di(uploaded_file):
    encoder = mini3di.Encoder()
    parser = PDBParser(QUIET=True)
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdb') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
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

uploaded_file = st.file_uploader("Choose a PDB file", type='pdb')

if uploaded_file is not None:
    with st.spinner('Processing...'):
        results = predict_3di(uploaded_file)
        
    if results:
        st.success("Prediction completed!")
        for result in results:
            with st.expander(f"Chain {result['chain_id']}"):
                st.code(result['sequence'])
                st.download_button(
                    label=f"Download Chain {result['chain_id']} sequence",
                    data=result['sequence'],
                    file_name=f"chain_{result['chain_id']}_3di.txt"
                )