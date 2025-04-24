import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Checklist Auto-Filter", layout="wide")
st.title("🧾 Checklist Auto-Filter")

uploaded_file = st.file_uploader("Upload your checklist (Excel file)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if "Description" not in df.columns or "Designer" not in df.columns:
        st.error("Excel must contain 'Description' and 'Designer' columns.")
    else:
        customers = ["Intel", "Xilinx", "AMD", "Nvidia"]

        def extract_customers(description):
            found = [cust for cust in customers if re.search(rf'\b{cust}\b', str(description), re.IGNORECASE)]
            return found if found else ["All"]

        df["Applies_To_Extracted"] = df["Description"].apply(extract_customers)
        all_projects = sorted(set(cust for sublist in df["Applies_To_Extracted"] for cust in sublist))
        selected_project = st.selectbox("Select Project Type", all_projects)

        def auto_fill_designer(row):
            applies = [cust.lower() for cust in row["Applies_To_Extracted"]]
            if selected_project.lower() in applies or "all" in applies:
                return row["Designer"]
            return "NA"

        df["Designer"] = df.apply(auto_fill_designer, axis=1)

        st.write("### Please Check the following Points in Your Design:")
        checkbox_states = {}
        for idx, row in df[df["Designer"].isna()].iterrows():
            checkbox_states[idx] = st.checkbox(row["Description"], key=f"checkbox_{idx}")

        for idx, checked in checkbox_states.items():
            if checked:
                df.loc[idx, "Designer"] = "Checked"

        df["Is_Relevant"] = df["Designer"] != "NA"
        df = df.sort_values(by="Is_Relevant", ascending=False).drop(columns=["Is_Relevant", "Applies_To_Extracted"])

        st.write("### Filtered Checklist (Relevant on Top)")
        st.dataframe(df, use_container_width=True)

        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        st.download_button(
            label="📥 Download Filtered Checklist",
            data=output,
            file_name=f"Checklist_{selected_project}_AutoNA.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
