import streamlit as st
import requests
from backend.utils.schema_merger import merge_input_groups
import pandas as pd

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="DocForge Hub",
    layout="wide"
)

st.title("DocForge Hub")
st.caption("Generate, Review, Approve & Publish Documents")

st.divider()

# ---------------- SESSION STATE ----------------

if "selected_draft_id" not in st.session_state:
    st.session_state.selected_draft_id = None

if "last_generated_id" not in st.session_state:
    st.session_state.last_generated_id = None

if "generation_in_progress" not in st.session_state:
    st.session_state.generation_in_progress = False

# ---------------- FIELD RENDERING ----------------

def render_field(label, field, key):
    field_type = field["type"]
    if field_type == "text":
        return st.text_input(label, key=key)
    elif field_type == "textarea":
        return st.text_area(label, key=key, height=100)
    elif field_type == "number":
        return st.number_input(label, key=key)
    elif field_type == "boolean":
        return st.checkbox(label, key=key)
    elif field_type == "date":
        return st.date_input(label, key=key)
    elif field_type == "dropdown":
        options = field.get("options", [])
        return st.selectbox(label, options, key=key)
    elif field_type == "multiselect":
        options = field.get("options", [])
        return st.multiselect(label, options, key=key)
    else:
        return st.text_input(label, key=key)


# ---------------- DYNAMIC FORM ----------------

def render_dynamic_form(base_groups, doc_groups, document_name):
    user_inputs = {}
    validation_errors = []

    st.markdown("## Document Details")
    st.divider()

    if base_groups:
        st.markdown("### 1. General Information")

        for group in base_groups:
            for field in group["fields"]:
                key = field["key"]
                label = field["label"]

                if field.get("required"):
                    label += " *"

                value = render_field(label, field, key)
                user_inputs[key] = value

                if field.get("required") and not value:
                    validation_errors.append(f"{field['label']} is required.")

        st.divider()

    if doc_groups:
        st.markdown(f"### 2. {document_name} Information")

        for group in doc_groups:
            st.markdown(f"**{group['group_name']}**")

            for field in group["fields"]:
                key = field["key"]
                label = field["label"]

                if field.get("required"):
                    label += " *"

                value = render_field(label, field, key)
                user_inputs[key] = value

                if field.get("required") and not value:
                    validation_errors.append(f"{field['label']} is required.")

            st.divider()

    return user_inputs, validation_errors

# SECTION VALIDATION BADGE HELPER

def section_quality_badge(section_validation: dict) -> str:
    if not section_validation:
        return ""
    if section_validation.get("valid"):
        wc = section_validation.get("word_count", 0)
        return f"   {wc} words"
    else:
        issues = section_validation.get("issues", [])
        return f"    {len(issues)} issue(s)"

# ---------------- STEP 1: DOCUMENT SELECTION ----------------

st.subheader("Select Document")

col1, col2, col3 = st.columns(3)

with col1:
    departments = [
    "HR",
    "IT Operations",
    "Legal",
    "Marketing",
    "Finance & Accounting",
    "Engineering",
    "Quality Assurance",
    "Security & Compliance",
    "Customer Success",
    "Product Management"
    ]

    department = st.selectbox("Department", departments)

response = requests.get(
    f"{API_BASE_URL}/documents/list",
    params={"department": department}
)

documents_meta = response.json() if response.status_code == 200 else []

with col2:
    document_types = sorted(set(doc["internal_type"] for doc in documents_meta))
    selected_type = st.selectbox("Document Type", ["ALL"] + document_types)

with col3:
    if selected_type == "ALL":
        filtered_docs = documents_meta
    else:
        filtered_docs = [
            doc for doc in documents_meta
            if doc["internal_type"] == selected_type
        ]

    if filtered_docs:
        document_label = st.selectbox(
            "Document",
            [doc["document_name"] for doc in filtered_docs]
        )
        document_filename = document_label
    else:
        document_filename = None

st.divider()


# ---------------- STEP 2: COMPANY PROFILE ----------------

with st.expander("Company Profile", expanded=True):
    company_name = st.text_input("Company Name")
    industry = st.text_input("Industry")
    employee_count = st.number_input("Employee Count", min_value=1)
    region = st.text_input("Operating Region")
    compliance = st.text_input("Compliance Frameworks")
    jurisdiction = st.text_input("Jurisdiction")
    founded_year = st.text_input("Founded Year")
    headquarters_location = st.text_input("Headquarters Location")
    ceo_name = st.text_input("CEO Name")
    cto_name = st.text_input("CTO Name")
    founders = st.text_area("Founders")
    company_background = st.text_area("Company Background")

st.divider()


# ---------------- STEP 3: LOAD DOCUMENT CONFIG ----------------

if document_filename:

    response = requests.post(
        f"{API_BASE_URL}/documents/preview",
        json={
            "department": department,
            "document_filename": document_filename
        }
    )

    if response.status_code != 200:
        st.error("Failed to load document.")
        st.stop()

    doc = response.json()
    # st.write("RAW DOC FROM BACKEND:", doc)
    merged_groups = merge_input_groups(doc)

    base_groups = []
    doc_groups = []

    for group in merged_groups:
        if group.get("source") == "base":
            base_groups.append(group)
        else:
            doc_groups.append(group)

    user_inputs, validation_errors = render_dynamic_form(
        base_groups,
        doc_groups,
        doc["document_name"]
    )

    st.divider()

    # ---------------- GENERATE BUTTON ----------------

    if st.button("Generate Draft", use_container_width=True):

        if not company_name or not industry or not region or not jurisdiction:
            st.error("Please complete company profile before generating.")
            st.stop()

        if validation_errors:
            for err in validation_errors:
                st.error(err)
            st.stop()

        for key, value in user_inputs.items():
            if hasattr(value, "isoformat"):
                user_inputs[key] = value.isoformat()

        response = requests.post(
            f"{API_BASE_URL}/documents/generate",
            json={
                "department": department.lower(),
                "document_filename": document_filename,
                "company_profile": {
                    "company_name": company_name,
                    "industry": industry,
                    "employee_count": employee_count,
                    "regions": [region],
                    "compliance_frameworks": [compliance],
                    "default_jurisdiction": jurisdiction,
                    "founded_year": founded_year,
                    "headquarters_location": headquarters_location,
                    "ceo_name": ceo_name,
                    "cto_name": cto_name,
                    "founders": founders,
                    "company_background": company_background
                },
                "document_inputs": user_inputs
            }
        )

        if response.status_code == 200:
            result = response.json()
            st.success("Draft Generated Successfully")
            st.session_state.selected_draft_id = result["draft_id"]
        else:
            st.error(f"Generation failed: {response.status_code}")
            st.error(response.text)


# ---------------- DRAFT LIBRARY (ALWAYS VISIBLE) ----------------

st.divider()
st.subheader("Draft Library")

response = requests.get(f"{API_BASE_URL}/documents/drafts")

if response.status_code == 200:
    drafts = response.json()

    if drafts:

    # Keep only latest draft per document_name
        unique_docs = {}

        for draft in drafts:
            name = draft["document_name"]

            if name not in unique_docs:
                unique_docs[name] = draft
            else:
                # Keep the latest version
                if draft["version"] > unique_docs[name]["version"]:
                    unique_docs[name] = draft

        filtered_drafts = list(unique_docs.values())

        for draft in filtered_drafts:
            col1, col2, col3, col4 = st.columns([4, 2, 1, 1])

            with col1:
                st.write(f"**{draft['document_name']}** (v{draft['version']})")

            with col2:
                st.write(draft["status"])

            with col3:
                if st.button("View", key=f"view_{draft['id']}"):
                    st.session_state.selected_draft_id = draft["id"]

            with col4:
                if st.button("Delete", key=f"delete_{draft['id']}"):
                    requests.delete(
                        f"{API_BASE_URL}/documents/draft/{draft['id']}"
                    )
                    st.success("Draft deleted")
                    st.experimental_rerun()
    else:
        st.info("No drafts found.")


# ---------------- SHOW FULL DOCUMENT CONTENT ----------------

if st.session_state.selected_draft_id:

    response = requests.get(
        f"{API_BASE_URL}/documents/draft/{st.session_state.selected_draft_id}"
    )

    if response.status_code == 200:
        draft_detail = response.json()

        st.divider()
        st.subheader("Section Review & Approval")

        total_sections = len(draft_detail["sections"])
        approved_sections = sum(
            1 for s in draft_detail["sections"]
            if s.get("status") == "approved"
        )

        progress_ratio = approved_sections / total_sections if total_sections else 0

        st.subheader("Review Progress")
        st.markdown(
            f"**{approved_sections} of {total_sections} Sections Confirmed**"
        )

        st.progress(progress_ratio)
        st.divider()

        all_approved = True

        for section in draft_detail["sections"]:

            # if section.get("status") != "approved":
            #     continue

            section_name = section["section_name"]
            section_status = section.get("status", "draft")
            blocks = section["content"]

            # 🔥 Handle old double-encoded data
            if isinstance(blocks, str):
                try:
                    import json
                    blocks = json.loads(blocks)
                except:
                    blocks = []

            if not isinstance(blocks, list):
                blocks = []

            st.markdown(f"## {section_name}")

            # 🔥 Status Badge
            if section_status == "approved":
                st.success("✅ Approved")
            else:
                st.warning("📝 Draft")
                all_approved = False

            # Render Content
            paragraph_text = ""

            for block in blocks:
                if isinstance(block, dict):

                    if block.get("type") == "paragraph":
                        paragraph_text += block.get("content", "") + "\n\n"

                    elif block.get("type") == "table":
                        df = pd.DataFrame(
                            block.get("rows", []),
                            columns=block.get("headers", [])
                        )
                        st.table(df)

            # ---------------- PREVIEW CARD ----------------

            st.markdown("##### Preview")

            if paragraph_text.strip():
                st.markdown(paragraph_text)

            # ---------------- ACTION ROW ----------------

            action_col1, action_col2, action_col3 = st.columns([1,1,2])

            # Edit toggle state
            edit_key = f"edit_mode_{draft_detail['id']}_{section_name}"
    
            if edit_key not in st.session_state:
                st.session_state[edit_key] = False

            is_editing = st.session_state[edit_key]


            with action_col1:
                if section_status != "approved":
                    if st.button("✏ Edit", key=f"toggle_edit_{draft_detail['id']}_{section_name}"):
                        st.session_state[edit_key] = True
                        st.rerun()


            with action_col2:
                if section_status != "approved":
                    if st.button("✓ Confirm", key=f"approve_{section_name}"):

                        requests.post(
                            f"{API_BASE_URL}/documents/approve-section",
                            params={
                                "draft_id": st.session_state.selected_draft_id,
                                "section_name": section_name
                            }
                        )

                        st.success("Section Locked")
                        st.rerun()

            # 🔄 Regenerate Section
            structured_sections = [
                "review & revision history",
                "acknowledgement",
                "acknowledgement and acceptance"
            ]

            if section_status != "approved" and section_name.lower() not in structured_sections:

                with action_col3:
                    feedback = st.text_input(
                        "Improvement Note",
                        key=f"feedback_{section_name}"
                    )

                    if st.button("🔄 Regenerate", key=f"regen_{section_name}"):

                        regen_response = requests.post(
                            f"{API_BASE_URL}/documents/regenerate-section",
                            params={
                                "draft_id": st.session_state.selected_draft_id,
                                "section_name": section_name,
                                "improvement_note": feedback
                            }
                        )

                        if regen_response.status_code == 200:
                            st.success("Section Regenerated")
                            st.rerun()
                        else:
                            st.error(regen_response.text)
            # ---------------- EDIT MODE AREA ----------------

            if is_editing and section_status != "approved":

                edited_text = st.text_area(
                    "Edit Section Content",
                    value=paragraph_text.strip(),
                    height=200,
                    key=f"edit_content_{draft_detail['id']}_{section_name}"
                )

                save_col1, save_col2 = st.columns([1,3])

                with save_col1:
                    if st.button("Save Changes", key=f"save_edit_{draft_detail['id']}_{section_name}"):

                        save_response = requests.post(
                            f"{API_BASE_URL}/documents/save-section-edit",
                            json={
                                "draft_id": st.session_state.selected_draft_id,
                                "section_name": section_name,
                                "updated_text": edited_text
                            }
                        )

                        if save_response.status_code == 200:
                            st.success("Changes Saved")

                            st.session_state[edit_key] = False

                            # 🔥 Clear textarea widget state
                            text_key = f"edit_content_{draft_detail['id']}_{section_name}"
                            if text_key in st.session_state:
                                del st.session_state[text_key]

                            st.rerun()

                        else:
                            st.error(save_response.text)

            # elif section_status != "approved" and section_name.lower() in structured_sections:
            #     st.info("Regeneration disabled for structured section.")
            # st.success("🎉 All sections approved. Document ready for export.")   
            st.divider()

        # 🔐 EXPORT SECTION
        st.subheader("Final Document Export")

        col1, col2, col3 = st.columns(3)

        if all_approved:

            with col1:
                if st.button("Download PDF"):
                    st.markdown(
                        f'<a href="{API_BASE_URL}/documents/export/{st.session_state.selected_draft_id}/pdf" target="_blank">Click here to download PDF</a>',
                        unsafe_allow_html=True
                    )

            with col2:
                if st.button("Download DOCX"):
                    st.markdown(
                        f'<a href="{API_BASE_URL}/documents/export/{st.session_state.selected_draft_id}/docx" target="_blank">Click here to download DOCX</a>',
                        unsafe_allow_html=True
                    )

            with col3:
                if st.button("Download XLS"):
                    st.markdown(
                        f'<a href="{API_BASE_URL}/documents/export/{st.session_state.selected_draft_id}/xls" target="_blank">Click here to download XLS</a>',
                        unsafe_allow_html=True
                    )

        # ---------------- FULL DOCUMENT PREVIEW ----------------

        if all_approved:

            st.divider()
            st.subheader("Full Document Preview")

            import json
            import pandas as pd

            for section in draft_detail["sections"]:

                section_name = section["section_name"]
                section_status = section.get("status", "draft")

                st.markdown(f"### {section_name}")

                if section_status == "approved":
                    st.success("🔒 Locked")
                else:
                    st.warning("📝 Draft")

                blocks = section.get("content", [])

                if isinstance(blocks, str):
                    try:
                        blocks = json.loads(blocks)
                    except:
                        blocks = []

                if not isinstance(blocks, list):
                    st.markdown("Invalid section format")
                    st.divider()
                    continue

                for block in blocks:

                    if not isinstance(block, dict):
                        continue

                    if block.get("type") == "paragraph":
                        st.markdown(block.get("content", ""))

                    elif block.get("type") == "table":

                        if section_name.lower() in [
                            "acknowledgement",
                            "acknowledgement and acceptance"
                        ]:
                            st.markdown("")
                            for row in block.get("rows", []):
                                label = row[0]
                                st.markdown(
                                    f"**{label}:** ____________________________"
                                )
                            st.markdown("")
                        else:
                            df = pd.DataFrame(
                                block.get("rows", []),
                                columns=block.get("headers", [])
                            )
                            st.table(df)

                st.divider()

        else:
            st.divider()
            st.info("Full document preview will be available after all sections are approved.")


    else:
        st.error("Failed to load draft")
