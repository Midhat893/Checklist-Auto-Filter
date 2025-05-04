import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Checklist Auto-Filter", layout="wide")
st.title("🧾 Checklist Auto-Filter")

uploaded_file = st.file_uploader("Upload your checklist (Excel file)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if "Description" not in df.columns or "Designer" not in df.columns or "S.No." not in df.columns:
        st.error("Excel must contain 'S.No.', 'Description' and 'Designer' columns.")
    else:
        customers = ["Intel", "Xilinx", "AMD", "Nvidia"]
        testers = ["93K", "T2K", "Ultraflex"]

        def get_base_serial(serial):
            match = re.match(r'^(\d+)', str(serial))
            return match.group(1) if match else str(serial)

        def extract_customers(description):
            found = [cust for cust in customers if re.search(rf'\b{cust}\b', str(description), re.IGNORECASE)]
            return found
        
        def extract_testers(description):
            found = []
            for test in testers:
                pattern = rf'\b{test}\b'
                if re.search(pattern, str(description), re.IGNORECASE):
                    found.append(test)
            return found

        df["Base_SNo"] = df["S.No."].apply(get_base_serial)
        df["Applies_To_Extracted"] = df["Description"].apply(extract_customers)
        df["Applies_To_ExtractedTester"] = df["Description"].apply(extract_testers)
        # print(df["Applies_To_ExtractedTester"])
        
        all_projects = sorted(set(cust for sublist in df["Applies_To_Extracted"] for cust in sublist))
        all_projects.append("All") 
        selected_project = st.selectbox("Select Project Type", sorted(set(all_projects)))
        
        all_testers = []
        for sublist in df["Applies_To_ExtractedTester"]:
            for test in sublist:
                all_testers.append(test)
        unique_testers =set(all_testers)
        all_proj_tester = sorted(unique_testers)
        all_proj_tester.append("All")
        selected_tester = st.selectbox("Select Tester Type", all_proj_tester)

        relevant_main_bases = set()
        for _, row in df.iterrows():
            sno = str(row["S.No."])
            base = get_base_serial(sno)
            is_main_point = sno == base
            applies = row["Applies_To_Extracted"]
            applies_tester = row["Applies_To_ExtractedTester"]

            if is_main_point:
                if not applies: 
                    relevant_main_bases.add(base)
                elif selected_project in applies and selected_tester in applies_tester:
                    relevant_main_bases.add(base)

        df["Designer"] = df["Base_SNo"].apply(lambda b: "" if b in relevant_main_bases else "NA")

        st.write("### Please Check the following Points in Your Design:")
        checkbox_states = {}
        for idx, row in df[df["Designer"] == ""].iterrows():
            checkbox_states[idx] = st.checkbox(row["Description"], key=f"checkbox_{idx}")

        for idx, checked in checkbox_states.items():
            if checked:
                df.loc[idx, "Designer"] = "Checked"

        df["Is_Relevant"] = df["Designer"] != "NA"
        df = df.sort_values(by="Is_Relevant", ascending=False).drop(
            columns=[
                "Is_Relevant",
                "Applies_To_Extracted",
                "Applies_To_ExtractedTester",
                "Base_SNo"
                ]
        )

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
