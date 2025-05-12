import streamlit as st
import pandas as pd
import re
from io import BytesIO

def Schematic():
    uploaded_file = st.file_uploader("Upload your checklist (Excel file)", type=["xlsm"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file, sheet_name='SCHEMATIC', usecols="A,B , D, E, F", skiprows=1)

        if "Description" not in df.columns or "D1" not in df.columns or "S.No" not in df.columns:
            st.error("Excel must contain 'S.No', 'Description' and 'D1' columns.")
        else:
            customers = ["Intel", "Xilinx", "AMD", "Nvidia", "Hi-Silicon", "Advantest", "Mellanox"]
            testers = ["93K", "T2K", "Ultraflex"]

            def get_base_serial(serial):
                match = re.match(r'^(\d+)', str(serial))
                return match.group(1) if match else str(serial)

            def extract_customers(description):
                description = str(description).lower()
                found = []
                ignore_phrases = [r'for reference.*?\b{}', r'for e.g..*?\b{}',r'for example.*?\b{}']
                for cust in customers:
                    cust_lower = cust.lower()
                    if any(re.search(p.format(re.escape(cust_lower)), description) for p in ignore_phrases):
                        continue
                    if re.search(rf'\b{cust_lower}\b', description, re.IGNORECASE):
                        found.append(cust)
                return found

            def extract_testers(description):
                description = str(description).lower()
                found = []
                ignore_phrases = [r'for reference.*?\b{}',
                                   r'for e.g..*?\b{}',
                                   r'For example.*?\b{}'
                                   ]
                for test in testers:
                    test_lower = test.lower()
                    if any(re.search(p.format(re.escape(test_lower)), description) for p in ignore_phrases):
                        continue
                    if re.search(rf'\b{test_lower}\b', description, re.IGNORECASE):
                        found.append(test)
                return found

            df["Base_SNo"] = df["S.No"].apply(get_base_serial)
            df["Applies_To_Extracted"] = df["Description"].apply(extract_customers)
            df["Applies_To_ExtractedTester"] = df["Description"].apply(extract_testers)

            current_heading = ""
            section_headings = []
            for _, row in df.iterrows():
                sno = str(row["S.No"]).strip()
                desc = str(row["Description"]).strip() if not pd.isna(row["Description"]) else ""
                if not sno or sno.lower() == "nan":
                    current_heading = desc
                section_headings.append(current_heading)
                
            df["Section_Heading"] = section_headings

            all_projects = sorted(set(cust for sublist in df["Applies_To_Extracted"] for cust in sublist))
            all_projects.append("All")
            selected_project = st.selectbox("Select Project Type", sorted(set(all_projects)))

            all_testers = [test for sublist in df["Applies_To_ExtractedTester"] for test in sublist]
            all_proj_tester = sorted(set(all_testers))
            all_proj_tester.append("All")
            selected_tester = st.selectbox("Select Tester Type", all_proj_tester)

            # Filter relevance based on section + base S.No
            relevant_main_bases = set()
            for _, row in df.iterrows():
                sno = str(row["S.No"]).strip()
                base = get_base_serial(sno)
                heading = row["Section_Heading"]
                is_main_point = sno == base
                applies = row["Applies_To_Extracted"]
                applies_tester = row["Applies_To_ExtractedTester"]

                if is_main_point:
                    project_match = selected_project in applies or selected_project == "All"
                    tester_match = selected_tester in applies_tester or selected_tester == "All"
                    # is_generic_project = len(applies) == 0
                    # is_generic_tester = len(applies_tester) == 0
                    is_generic = len(applies) == 0 and len(applies_tester) == 0

                    if project_match or tester_match or is_generic:
                        relevant_main_bases.add((heading, base))

            def mark_relevance(row):
                sno = str(row["S.No"]).strip()
                base = row["Base_SNo"]
                heading = row["Section_Heading"]
                if not sno or sno.lower() == "nan":
                    return ""  
                return "" if (heading, base) in relevant_main_bases else "NA"

            df["D1"] = df.apply(mark_relevance, axis=1)

            st.write("### Please Check the following Points in Your Design:")
            checkbox_states = {}

            # Group by section heading
            for heading, group in df[df["D1"] == ""].groupby("Section_Heading", sort=False):
                # Filter out actual checklist points (non-heading rows)
                points = group[group["S.No"].notna() & (group["S.No"].astype(str).str.strip().str.lower() != "nan")]

                if points.empty:
                    continue  # Skip if no points to show

                with st.expander(f"**{heading}**"):
                    for idx, row in points.iterrows():
                        desc = str(row["Description"]).strip()
                        if desc:
                            checkbox_states[idx] = st.checkbox(desc, key=f"checkbox_{idx}")

                    

            for idx, checked in checkbox_states.items():
                if checked:
                    df.loc[idx, "D1"] = "Checked"

            df["Is_Relevant"] = df["D1"] != "NA"
            df = df.drop(columns=[
                "Is_Relevant",
                "Applies_To_Extracted",
                "Applies_To_ExtractedTester",
                "Base_SNo",
                "Section_Heading"
            ])

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
