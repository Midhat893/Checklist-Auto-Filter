import streamlit as st
from Schematic import Schematic
# from BOM import BOM

st.set_page_config(page_title="Checklist Auto-Filter", layout="wide")

st.title("🧾 Checklist Auto-Filter")
tab1, tab2 = st.tabs(["SCHEMATIC", "BOM"])

with tab1:
    tab1.subheader("SCHEMATIC")
    Schematic()

with tab2:
    tab2.subheader("Please Check these Points in Your BOM")
    # BOM()
