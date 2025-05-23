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
            
            def is_relay_related(description):
                description = str(description).lower()
                ignore_phrases = [r'and/or.*?\b{}']
                for pattern in ignore_phrases:
                    if re.search(pattern,description):
                        return False
                return 'relay' in description
            
            def extract_customers(description):
                description = str(description).lower()
                found = []
                ignore_phrases = [r'for reference.*?\b{}', r'for e.g..*?\b{}',r'for example.*?\b{}', r'QA Only.*?\b{}']
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

            uses_relays = st.checkbox("Does your design use relays")

            valid_section_headings = set()
            for heading in df["Section_Heading"].unique(): 
                heading_lower = str(heading).lower()

                heading_customers = extract_customers(heading_lower)
                heading_testers = extract_testers(heading_lower)

                is_generic_heading = not heading_customers and not heading_testers

                if (
                    selected_project in heading_customers or
                    selected_tester in heading_testers or
                    is_generic_heading
                ):
                    valid_section_headings.add(heading)

            relevant_main_bases = set()
            for _, row in df.iterrows():
                sno = str(row["S.No"]).strip()
                base = get_base_serial(sno)
                heading = row["Section_Heading"]
                is_main_point = sno == base
                applies = row["Applies_To_Extracted"]
                applies_tester = row["Applies_To_ExtractedTester"]

                if is_main_point and heading in valid_section_headings:
                    project_match = selected_project in applies or selected_project == "All"
                    tester_match = selected_tester in applies_tester or selected_tester == "All"
                    def QA_Points(description):
                        description = str(description).strip().lower()
                        return not re.search(r'qa only', description, re.IGNORECASE)

                    is_generic = len(applies) == 0 and len(applies_tester) == 0 and QA_Points(row["Description"])

                    if project_match or tester_match or is_generic:
                        relevant_main_bases.add((heading, base))

            def mark_relevance(row):
                sno = str(row["S.No"]).strip()
                base = row["Base_SNo"]
                heading = row["Section_Heading"]
                if not sno or sno.lower() == "nan":
                    return ""  
                if not uses_relays and is_relay_related(row["Description"]):
                    return "NA"
                return "" if (heading, base) in relevant_main_bases else "NA"

            df["D1"] = df.apply(mark_relevance, axis=1)

            st.write("### Please Check the following Points in Your Design:")
            checkbox_states = {}

            # Group by section heading
            for heading, group in df[df["D1"] == ""].groupby("Section_Heading", sort=False):
                # Filter out actual checklist points (non-heading rows)
                points = group[group["S.No"].notna() & (group["S.No"].astype(str).str.strip().str.lower() != "nan")]

                if points.empty:
                    continue  

                with st.expander(f"**{heading}**"):
                    for idx, row in points.iterrows():
                        desc = str(row["Description"]).strip()
                        if desc:
                            with st.container():
                                st.markdown(
                                    f"""
                                    <div style="
                                        border: 0px solid #6e6e6e;
                                        border-radius: 5px;
                                        padding: 0.05px;
                                        margin-bottom: -1px;
                                        background-color: #6e6e6e;
                                        box-shadow: 1px 1px 5px rgba(0, 0, 0, 0.1);
                                    ">
                                    """,
                                    unsafe_allow_html=True
                                )
                                checkbox_states[idx] = st.checkbox(desc, key=f"checkbox_{idx}")
                                st.markdown("</div>", unsafe_allow_html=True)
                            

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
