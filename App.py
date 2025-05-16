import streamlit as st
from Schematic import Schematic
from BOM import BOM

st.set_page_config(page_title="Checklist Auto-Filter", layout="wide")

st.title("🧾 Checklist Auto-Filter")
tab1, tab2, tab3 = st.tabs(["Welcome Page","SCHEMATIC", "BOM"])

with tab1:
    tab1.subheader("CHECKLIST FOR DESIGN AND QA")
    uploaded_file = st.file_uploader("Upload your checklist (Excel file)", type=["xlsm"])
    if uploaded_file:
        st.session_state["uploaded_file"] = uploaded_file
    name = st.text_input("Designer Name: ")

with tab2:
    tab2.subheader("SCHEMATIC")
    Schematic()

with tab3:
    tab3.subheader("BOM")
    BOM()
