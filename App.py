import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Checklist Auto-Filter", layout="wide")
st.title("🧾 Checklist Auto-Filter")

uploaded_file = st.file_uploader("Upload your checklist (Excel file)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if "Applies To" not in df.columns or "Designer" not in df.columns:
        st.error("Excel must contain 'Applies To' and 'Designer' columns.")
    else:
        project_types = df["Applies To"].dropna().str.split(',').explode().str.strip().unique()
        selected_project = st.selectbox("Select Project Type", sorted(project_types))

#Main Function
        def auto_fill_designer(row):
            applies = str(row["Applies To"]).lower()
            if selected_project.lower() in applies or "all" in applies:
                return row["Designer"]
            return "NA"

        df["Designer"] = df.apply(auto_fill_designer, axis=1)
        
        df["Is_Relevant"] = df["Designer"] != "NA"
        relevant_df = df[df["Is_Relevant"]].copy()
        non_relevant_df = df[~df["Is_Relevant"]].copy()
        
        # Add a checkbox column to relevant rows
        relevant_df["Selected"] = False
        edited_relevant_df = st.data_editor(relevant_df, use_container_width=True, num_rows="dynamic")
        # Merge back everything
        final_df = pd.concat([edited_relevant_df, non_relevant_df], ignore_index=True)
        final_df = final_df.drop(columns=["Is_Relevant"])

        output_df = final_df.drop(columns=["Applies To"])

        st.write("### Filtered Checklist (Relevant on Top)")
        st.dataframe(final_df.drop(columns=["Applies To"]), use_container_width=True)

        output = BytesIO()
        output_df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        st.download_button(
            label="📥 Download Filtered Checklist",
            data=output,
            file_name=f"Checklist_{selected_project}_AutoNA.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
