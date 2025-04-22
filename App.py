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

        # df["Is_Relevant"] = df["Designer"] != "NA"
        # df = df.sort_values(by="Is_Relevant", ascending=False).drop(columns=["Is_Relevant"])
        
        editable_df = df[df["Designer"].isna()].reset_index(drop=False)
        checkbox_states = {}
        
        st.write("### Please Check the following Points in Your Design:")
        for idx, row in df[df["Designer"].isna()].iterrows():
            checkbox_label = f"{row['Description']}"
            checkbox_states[idx] = st.checkbox(checkbox_label, key=f"checkbox_{idx}")
            
        for idx, row in df[df["Designer"].isna()].iterrows():
            if checkbox_states[idx]:
                df.loc[idx, "Designer"] = "Checked"
        
        df["Is_Relevant"] = df["Designer"] != "NA"
        df = df.sort_values(by="Is_Relevant", ascending=False).drop(columns=["Is_Relevant"])

        output_df = df.drop(columns=["Applies To"])

        st.write("### Filtered Checklist (Relevant on Top)")
        st.dataframe(output_df, use_container_width=True)

        output = BytesIO()
        output_df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        st.download_button(
            label="📥 Download Filtered Checklist",
            data=output,
            file_name=f"Checklist_{selected_project}_AutoNA.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
