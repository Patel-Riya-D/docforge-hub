"""
ui.py

Frontend UI module for DocForge Hub built using Streamlit.

This module provides an interactive interface for:
- Document generation (multi-step wizard)
- Draft review, editing, and approval
- Exporting documents (DOCX)
- Publishing to Notion
- Viewing draft library
- RAG-based knowledge search (CiteRAG Lab)

Key Features:
- Multi-step form wizard with validation
- Dynamic form rendering using schema merger
- AI-powered question generation for missing inputs
- Section-level editing, approval, and regeneration
- Integration with backend APIs (FastAPI)
- RAG tools: search, compare, summarize, evaluation

Tabs:
1. Generate Draft → Create new documents
2. Draft Library → Manage saved drafts
3. CiteRAG Lab → Knowledge retrieval & analysis

This module acts as the user interaction layer of DocForge Hub,
connecting UI with backend AI services.

Main Application Flow:

1. Sidebar:
    - Select department and document template

2. Generate Draft Tab:
    - Multi-step wizard:
        Step 1 → Company profile
        Step 2 → Document inputs (merged schema)
        Step 3 → AI clarification questions
        Step 4 → Generate draft via backend

3. Draft Review:
    - Section editing, approval, regeneration
    - Export and publish

4. Draft Library:
    - View, delete, manage drafts

5. CiteRAG Lab:
    - Search → Ask questions
    - Compare → Compare documents
    - Summarize → Generate summaries
    - Evaluate → Run RAG metrics
    
"""

import os
import streamlit as st
import requests
from backend.utils.schema_merger import merge_input_groups
import pandas as pd
from backend.generation.question_label_enhancer import enhance_label
from datetime import datetime, date
import json

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# -------------------- UI CONFIG --------------------
st.set_page_config(
    page_title="DocForge Hub",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- SESSION STATE --------------------
if "selected_draft_id" not in st.session_state:
    st.session_state.selected_draft_id = None
if "last_generated_id" not in st.session_state:
    st.session_state.last_generated_id = None
if "generation_in_progress" not in st.session_state:
    st.session_state.generation_in_progress = False
if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "form_data" not in st.session_state:
    st.session_state.form_data = {}
if "company_profile" not in st.session_state:
    st.session_state.company_profile = {
        "company_name": "",
        "industry": "",
        "employee_count": 100,
        "region": "",
        "compliance": "",
        "jurisdiction": "",
        "founded_year": "",
        "headquarters_location": "",
        "ceo_name": "",
        "cto_name": "",
        "founders": "",
        "company_background": ""
    }

# Original AI‑related session states
if "pending_questions" not in st.session_state:
    st.session_state.pending_questions = []
if "question_answers" not in st.session_state:
    st.session_state.question_answers = {}
if "questions_generated" not in st.session_state:
    st.session_state.questions_generated = False
if "questions_initialized" not in st.session_state:
    st.session_state.questions_initialized = False

# -------------------- HELPER FUNCTIONS --------------------
def format_date(date_string):
    """
    Format ISO date string into human-readable format.

    Args:
        date_string (str): ISO formatted date string.

    Returns:
        str: Formatted date string.

    Notes:
        - Handles timezone conversion
        - Returns original string if parsing fails
    """
    try:
        date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return date_obj.strftime("%B %d, %Y at %I:%M %p")
    except:
        return date_string

def render_field(label, field, key):
    """
    Render a dynamic form field based on its type.

    Args:
        label (str): Field label.
        field (dict): Field configuration (type, options, etc.).
        key (str): Unique Streamlit key.

    Returns:
        Any: User input value.

    Supported Types:
        - text
        - textarea
        - number
        - boolean
        - date
        - dropdown
        - multiselect
    """
    field_type = field["type"]
    existing_value = st.session_state.get(key, None)

    if field_type == "text":
        return st.text_input(
            label,
            key=key,
            value=existing_value if existing_value else ""
        )

    elif field_type == "textarea":
        return st.text_area(
            label,
            key=key,
            value=existing_value if existing_value else "",
            height=100
        )

    elif field_type == "number":
        return st.number_input(
            label,
            key=key,
            value=existing_value if existing_value else 0
        )

    elif field_type == "boolean":
        return st.checkbox(
            label,
            key=key,
            value=existing_value if existing_value else False
        )

    elif field_type == "date":
        return st.date_input(
            label,
            key=key,
            value=existing_value if existing_value else None
        )

    elif field_type == "dropdown":
        return st.selectbox(
            label,
            field.get("options", []),
            key=key,
            index=field.get("options", []).index(existing_value) if existing_value in field.get("options", []) else 0
        )

    elif field_type == "multiselect":
        return st.multiselect(
            label,
            field.get("options", []),
            key=key,
            default=existing_value if existing_value else []
        )

    else:
        return st.text_input(
            label,
            key=key,
            value=existing_value if existing_value else ""
        )

def render_company_step():
    """
    Render company profile input step.

    Collects:
        - Company details (name, industry, region, etc.)
        - Leadership info (CEO, CTO)
        - Background information

    Behavior:
        - Displays form in card layout
        - Updates session state with inputs

    Notes:
        - Mandatory fields are validated later
        - Used as first step in document generation wizard
    """

    with st.container(border=True):
        col1, col2 = st.columns([1, 11])
        with col1:
            st.markdown("# 🏢")
        with col2:
            st.subheader("Company Profile")
            st.caption("Fields marked with * are mandatory and will be embedded into the document.")
    
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name *", key="company_name", value=st.session_state.company_profile.get("company_name", ""))
        industry = st.text_input("Industry *", key="industry", value=st.session_state.company_profile.get("industry", ""))
        employee_count = st.number_input("Employee Count", min_value=1, key="employee_count", value=st.session_state.company_profile.get("employee_count", 100))
        region = st.text_input("Operating Region *", key="region", value=st.session_state.company_profile.get("region", ""))
        compliance = st.text_input("Compliance Framework", key="compliance", value=st.session_state.company_profile.get("compliance", ""))
        jurisdiction = st.text_input("Jurisdiction *", key="jurisdiction", value=st.session_state.company_profile.get("jurisdiction", ""))
    with col2:
        founded_year = st.text_input("Founded Year", key="founded_year", value=st.session_state.company_profile.get("founded_year", ""))
        headquarters_location = st.text_input("Headquarters Location", key="headquarters_location", value=st.session_state.company_profile.get("headquarters_location", ""))
        ceo_name = st.text_input("CEO Name", key="ceo_name", value=st.session_state.company_profile.get("ceo_name", ""))
        cto_name = st.text_input("CTO Name", key="cto_name", value=st.session_state.company_profile.get("cto_name", ""))
        founders = st.text_area("Founders", key="founders", value=st.session_state.company_profile.get("founders", ""))
        company_background = st.text_area("Company Background", key="company_background", value=st.session_state.company_profile.get("company_background", ""))
    
    # Update session state
    st.session_state.company_profile.update({
        "company_name": company_name,
        "industry": industry,
        "employee_count": employee_count,
        "region": region,
        "compliance": compliance,
        "jurisdiction": jurisdiction,
        "founded_year": founded_year,
        "headquarters_location": headquarters_location,
        "ceo_name": ceo_name,
        "cto_name": cto_name,
        "founders": founders,
        "company_background": company_background
    })
    # For AI questions we need the formatted name
    st.session_state.formatted_company_name = company_name.title() if company_name else ""

def render_document_step(step_idx, group, doc_name):
    """
    Render a document input group step.

    Features:
        - Dynamic field rendering
        - AI label enhancement for better UX
        - Validation for required fields

    Args:
        step_idx (int): Step index.
        group (dict): Input group schema.
        doc_name (str): Document name.

    Returns:
        tuple:
            - user_inputs (dict)
            - validation_errors (list)

    Notes:
        - Uses enhance_label() for improved questions
        - Supports multiple field types
    """
    with st.container(border=True):
        col1, col2 = st.columns([1, 11])
        with col1:
            # Directly use the icon from group, defaulting to 📄 if missing
            st.markdown(f"# {group.get('icon', '📄')}")
        with col2:
            st.subheader(group['group_name'])
            st.caption(group.get('description', ''))
    
    fields = group["fields"]
    user_inputs = {}
    validation_errors = []

    for idx, field in enumerate(fields):
        key = field["key"]
        raw_label = field["label"]

        # Label enhancement
        cache_key = f"enhanced_{doc_name}_{raw_label}"
        if cache_key not in st.session_state:
            st.session_state[cache_key] = enhance_label(raw_label, doc_name)

        label = st.session_state[cache_key]

        if field.get("required"):
            label = f"{label} *"

        # ✅ SINGLE COLUMN (no cols)
        value = render_field(label, field, f"step_{step_idx}_{key}")

        user_inputs[key] = value

        if field.get("required") and not value:
            validation_errors.append(f"{field['label']} is required.")

        # ✅ Optional spacing (clean UI)
        st.divider()

    return user_inputs, validation_errors

# -------------------- DRAFT REVIEW RENDERING FUNCTION --------------------
def render_draft_review(draft_detail, prefix=""):
    """
    Render draft review and approval interface.

    Features:
        - Section-by-section preview
        - Edit, approve, and regenerate sections
        - Progress tracking (approved vs pending)
        - Full document preview
        - Export (DOCX)
        - Publish to Notion

    Args:
        draft_detail (dict): Draft data from backend.
        prefix (str): Prefix for unique Streamlit keys.

    Behavior:
        - Displays content blocks (paragraphs, tables, diagrams)
        - Allows user interaction for refinement
        - Enables final export only after all sections are approved

    Notes:
        - Core review workflow of the system
        - Supports diagram rendering and tables
    """
    st.divider()
    
    # ----- Section Review & Approval -----
    st.subheader("Section Review & Approval")
    total_sections = len(draft_detail["sections"])
    approved_sections = sum(1 for s in draft_detail["sections"] if s.get("status") == "approved")
    progress_ratio = approved_sections / total_sections if total_sections else 0
    
    # UI: Use metrics and progress bar for overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sections", total_sections)
    with col2:
        st.metric("Approved", approved_sections)
    with col3:
        st.metric("Pending", total_sections - approved_sections)
    
    st.progress(progress_ratio, text=f"{approved_sections} of {total_sections} sections confirmed")
    st.divider()
    
    all_approved = True
    for section in draft_detail["sections"]:
        section_name = section["section_name"]
        section_status = section.get("status", "draft")
        blocks = section.get("blocks", [])
        
        # Handle old double-encoded data
        if isinstance(blocks, str):
            try:
                blocks = json.loads(blocks)
            except:
                blocks = []
        if not isinstance(blocks, list):
            blocks = []
        
        # UI: Use status badges in section header
        with st.container(border=True):
            col1, col2 = st.columns([10, 2])
            with col1:
                st.markdown(f"## {section_name}")
            with col2:
                if section_status == "approved":
                    st.success("✅ Approved")
                else:
                    st.warning("📝 Draft")
                    all_approved = False
            
            # Render content
            paragraph_text = ""
            for block in blocks:
                if isinstance(block, dict):
                    if block.get("type") == "paragraph":
                        paragraph_text += block.get("content", "") + "\n\n"
                    elif block.get("type") in ["bullet", "bulleted_list_item"]:
                        paragraph_text += f"- {block.get('content')}\n"
                    elif block.get("type") == "table":
                        df = pd.DataFrame(block.get("rows", []), columns=block.get("headers", []))
                        st.table(df)
                    elif block.get("type") == "diagram":
                        diagram_url = block.get("diagram_url")
                        image_path = block.get("render_path")
                        if diagram_url:
                            if diagram_url.startswith(('http://', 'https://')):
                                full_url = diagram_url
                            else:
                                full_url = f"{API_BASE_URL}{diagram_url}"
                            col_l, col_m, col_r = st.columns([1, 3, 1])
                            with col_m:
                                st.image(full_url, width=600)
                        elif image_path and os.path.exists(image_path):
                            with open(image_path, "rb") as f:
                                st.image(f.read(), width=600)
                        else:
                            st.warning("Diagram not available")
            
            st.markdown("##### Preview")
            if paragraph_text.strip():
                with st.container(border=True):
                    st.markdown(paragraph_text)
            
            # Action row (Edit, Confirm, Regenerate)
            action_col1, action_col2, action_col3 = st.columns([1,1,2])
            # Include prefix in session state key
            edit_key = f"{prefix}_edit_mode_{draft_detail['id']}_{section_name}"
            if edit_key not in st.session_state:
                st.session_state[edit_key] = False
            is_editing = st.session_state[edit_key]
            
            with action_col1:
                if section_status != "approved":
                    if st.button("✏ Edit", key=f"{prefix}_toggle_edit_{draft_detail['id']}_{section_name}"):
                        st.session_state[edit_key] = True
                        st.rerun()
            with action_col2:
                if section_status != "approved":
                    if st.button("✓ Confirm", key=f"{prefix}_approve_{draft_detail['id']}_{section_name}"):
                        with st.spinner("Approving..."):
                            requests.post(
                                f"{API_BASE_URL}/documents/approve-section",
                                params={"draft_id": draft_detail['id'], "section_name": section_name}
                            )
                        st.success("Section Locked")
                        st.rerun()
            
            # Regenerate section
            structured_sections = [
                "review & revision history", 
                "acknowledgement", 
                "acknowledgement and acceptance",
                "form",
                "title",
                "signature"
            ]
            if section_status != "approved" and section_name.lower() not in structured_sections:
                with action_col3:
                    feedback = st.text_input("Improvement Note", key=f"{prefix}_regen_input_{draft_detail['id']}_{section_name}")
                    if st.button("🔄 Regenerate", key=f"{prefix}_regen_button_{draft_detail['id']}_{section_name}"):
                        with st.spinner("Regenerating section..."):
                            regen_response = requests.post(
                                f"{API_BASE_URL}/documents/regenerate-section",
                                params={"draft_id": draft_detail['id'], "section_name": section_name, "improvement_note": feedback}
                            )
                        if regen_response.status_code == 200:
                            st.success("Section Regenerated")
                            st.rerun()
                        else:
                            st.error(regen_response.text)
            
            # Edit mode area
            if is_editing and section_status != "approved":
                edited_text = st.text_area(
                    "Edit Section Content",
                    value=paragraph_text.strip(),
                    height=200,
                    key=f"{prefix}_edit_content_{draft_detail['id']}_{section_name}"
                )
                save_col1, save_col2 = st.columns([1,3])
                with save_col1:
                    if st.button("Save Changes", key=f"{prefix}_save_edit_{draft_detail['id']}_{section_name}"):
                        with st.spinner("Saving..."):
                            save_response = requests.post(
                                f"{API_BASE_URL}/documents/save-section-edit",
                                json={
                                    "draft_id": draft_detail['id'],
                                    "section_name": section_name,
                                    "updated_text": edited_text
                                }
                            )
                        if save_response.status_code == 200:
                            st.success("Changes Saved")
                            st.session_state[edit_key] = False
                            # Clear the text area value from session state
                            text_key = f"{prefix}_edit_content_{draft_detail['id']}_{section_name}"
                            if text_key in st.session_state:
                                del st.session_state[text_key]
                            st.rerun()
                        else:
                            st.error(save_response.text)
    
    # ----- Export buttons (only DOCX kept) -----
    st.subheader("Final Document Export")
    col1, col2, col3 = st.columns([1, 1, 3])
    if all_approved:
        with col1:
            docx_url = f"{API_BASE_URL}/documents/export/{draft_detail['id']}/docx"
            response = requests.get(docx_url)
            if response.status_code == 200:
                st.download_button(
                    "📥 Download DOCX",
                    data=response.content,
                    file_name="document.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key=f"{prefix}_download_{draft_detail['id']}"   
                )
            else:
                st.error(f"❌ Download failed: {response.text}")
    else:
        st.info("All sections must be approved before export.")
    
    # ----- Full Document Preview -----
    if all_approved:
        st.divider()
        st.subheader("Full Document Preview")
        expand_all = st.checkbox("Expand all sections", value=False, key=f"{prefix}_expand_all_{draft_detail['id']}")
        for section in draft_detail["sections"]:
            section_name = section["section_name"]
            with st.expander(f"📄 {section_name}", expanded=expand_all):
                blocks = section.get("blocks", [])
                if isinstance(blocks, str):
                    try:
                        blocks = json.loads(blocks)
                    except:
                        blocks = []
                if not isinstance(blocks, list):
                    st.markdown("Invalid section format")
                    continue
                for block in blocks:
                    if isinstance(block, dict):
                        if block.get("type") == "paragraph":
                            st.markdown(block.get("content", ""))
                        elif block.get("type") in ["bullet", "bulleted_list_item"]:
                            st.markdown(f"- {block.get('content')}")
                        elif block.get("type") == "table":
                            if section_name.lower() in ["acknowledgement", "acknowledgement and acceptance"]:
                                for row in block.get("rows", []):
                                    label = row[0]
                                    st.markdown(f"**{label}:** ____________________________")
                            else:
                                df = pd.DataFrame(block.get("rows", []), columns=block.get("headers", []))
                                st.table(df)
                        elif block.get("type") == "diagram":
                            diagram_url = block.get("diagram_url")
                            image_path = block.get("render_path")
                            if diagram_url:
                                if diagram_url.startswith(('http://', 'https://')):
                                    full_url = diagram_url
                                else:
                                    full_url = f"{API_BASE_URL}{diagram_url}"
                                st.image(full_url, width=600)
                            elif image_path and os.path.exists(image_path):
                                with open(image_path, "rb") as f:
                                    st.image(f.read(), width=600)
                            else:
                                st.warning("Diagram not available")
    else:
        st.divider()
        st.info("Full document preview will be available after all sections are approved.")
    
    if all_approved:
        # ----------------Publish doc to notion-------------------
        st.divider()
        st.subheader("Publish Document")
        col1, col2 = st.columns([1,3])
        with col1:
            if st.button("Publish to Notion", use_container_width=True, key=f"{prefix}_publish_{draft_detail['id']}"):
                with st.spinner("Publishing document to Notion..."):
                    publish_response = requests.post(
                        f"{API_BASE_URL}/documents/publish-notion/{draft_detail['id']}"
                    )
                if publish_response.status_code == 200:
                    st.success("Document successfully published to Notion 🎉")
                else:
                    st.error("Failed to publish document to Notion")

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.title("⚡ DocForge Hub")
    st.caption("AI-Powered Document Generation")
    
    st.divider()
    
    st.subheader("📍 Document")
    departments = [
        "HR", "IT Operations", "Legal", "Marketing", "Finance & Accounting",
        "Engineering", "Quality Assurance", "Security & Compliance",
        "Customer Success", "Product Management"
    ]
    department = st.selectbox("Department", departments, key="sidebar_department", label_visibility="collapsed")

    try:
        response = requests.get(f"{API_BASE_URL}/documents/list", params={"department": department})
        documents_meta = response.json() if response.status_code == 200 else []
    except:
        documents_meta = []
        st.warning("⚠️ Backend connection failed – using cached data (if any)")

    document_types = sorted(set(doc["internal_type"] for doc in documents_meta))
    selected_type = st.selectbox("Document Type", ["ALL"] + document_types, key="sidebar_doc_type", label_visibility="collapsed")

    filtered_docs = documents_meta if selected_type == "ALL" else [doc for doc in documents_meta if doc["internal_type"] == selected_type]
    document_filename = st.selectbox("Document Template", [doc["document_name"] for doc in filtered_docs], key="sidebar_document", label_visibility="collapsed") if filtered_docs else None
    
    if document_filename:
        st.info(f"Selected: {document_filename}")
    
    st.caption(
        "💡 Default is Latest (recommended). Select a specific version only if needed."
    )
# -------------------- MAIN CONTENT --------------------

st.header("⚡ DocForge Hub")
st.caption("Intelligent document generation platform powered by AI")

tabs = st.tabs(["✨ Generate Draft", "📚 Draft Library", "🔎 CiteRag Lab", "🤖 StateCase Assistant"])
tab_gen = tabs[0]
tab_lib = tabs[1]
tab_rag = tabs[2]
tab_statecase = tabs[3]

# ==================== GENERATE DRAFT TAB ====================
with tab_gen:
    if document_filename:
        # Reset wizard state when document changes (original logic)
        if st.session_state.get("current_doc") != document_filename:
            st.session_state.current_doc = document_filename
            st.session_state.current_step = 0
            st.session_state.form_data = {}
            st.session_state.pending_questions = []
            st.session_state.question_answers = {}
            st.session_state.questions_generated = False
            st.session_state.questions_initialized = False
            for k in list(st.session_state.keys()):
                if k.startswith("aiq_"):
                    del st.session_state[k]

        try:
            # Fetch document configuration
            with st.spinner("Loading document configuration..."):
                response = requests.post(f"{API_BASE_URL}/documents/preview", 
                                       json={"department": department, "document_filename": document_filename})
            
            if response.status_code == 200:
                doc_config = response.json()
                merged_groups = merge_input_groups(doc_config)
                
                base_groups = [g for g in merged_groups if g.get("source") == "base"]
                doc_groups = [g for g in merged_groups if g.get("source") != "base"]
                
                # --- MERGE DOCUMENT GROUPS INTO LARGER STEPS ---
                all_doc_groups = base_groups + doc_groups
                doc_step_count = 2  # Section 1 (static) + Section 2 (AI)
                total_steps = 1 + doc_step_count   # company + merged doc steps + AI questions
                current_step = st.session_state.current_step
                
                # UI: Progress bar with descriptive text
                progress_text = f"Step {current_step + 1} of {total_steps}"
                st.progress((current_step + 1) / total_steps, text=progress_text)
                
                # UI: Step indicators using columns with status icons
                step_names = ["🏢 Company"] + [f"📄 Section {i+1}" for i in range(doc_step_count)]
                cols = st.columns(total_steps)
                for i, col in enumerate(cols):
                    with col:
                        if i == current_step:
                            st.info(f"**{step_names[i]}**")
                        elif i < current_step:
                            st.success(f"✅ {step_names[i]}")
                        else:
                            st.write(f"⏳ {step_names[i]}")
                
                st.divider()
                
                # Render current step
                validation_errors = []
                if current_step == 0:
                    # Company profile step
                    render_company_step()
                elif current_step == 1:
                    # ✅ SECTION 1 → ALL STATIC QUESTIONS

                    for idx, group in enumerate(all_doc_groups):
                        if 'icon' not in group:
                            group['icon'] = "📄"
                        if 'description' not in group:
                            group['description'] = f"{doc_config['document_name']} details"

                        user_inputs, errs = render_document_step(idx, group, doc_config['document_name'])
                        validation_errors.extend(errs)

                        for key, value in user_inputs.items():
                            st.session_state.form_data[f"{idx}_{key}"] = value

                    # ✅ ADD THIS: Inject AI questions into LAST section only
                elif current_step == 2:
                    st.subheader("🤖 AI Generated Questions")
                    st.info("Answer AI-generated questions based on your inputs.")

                    # Generate questions once
                    if not st.session_state.pending_questions and not st.session_state.questions_generated:

                        all_inputs = {}
                        for step in range(len(all_doc_groups)):
                            for field in all_doc_groups[step]["fields"]:
                                key = f"step_{step}_{field['key']}"
                                if key in st.session_state:
                                    all_inputs[field['key']] = st.session_state[key]

                        safe_inputs = {
                            k: v.isoformat() if hasattr(v, "isoformat") else v
                            for k, v in all_inputs.items()
                        }

                        with st.spinner("Generating AI questions..."):
                            questions_response = requests.post(
                                f"{API_BASE_URL}/documents/generate-questions",
                                json={
                                    "department": department.lower(),
                                    "document_filename": document_filename,
                                    "company_profile": st.session_state.company_profile,
                                    "document_inputs": safe_inputs
                                }
                            )

                        if questions_response.status_code == 200:
                            st.session_state.pending_questions = questions_response.json().get("questions", [])
                            st.session_state.questions_generated = True

                    # Render AI questions
                    for i, q in enumerate(st.session_state.pending_questions):
                        key = q["key"]
                        question_text = q["question"]

                        unique_key = f"aiq_{i}_{key}"

                        if q.get("type") == "textarea":
                            st.text_area(question_text, key=unique_key)
                        else:
                            st.text_input(question_text, key=unique_key)
                
                # Navigation buttons
                st.divider()
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                with col1:
                    if current_step > 0:
                        if st.button("◀ Previous", use_container_width=True):
                            st.session_state.current_step -= 1
                            st.rerun()
                
                with col5:
                    if current_step < total_steps - 1:
                        if st.button("Next ▶", use_container_width=True, type="primary"):
                            # Validate only if on a document step (not company or AI)
                            if 0 < current_step <= doc_step_count and validation_errors:
                                for err in validation_errors:
                                    st.error(f"❌ {err}")
                            else:
                                st.session_state.current_step += 1
                                st.rerun()
                    else:
                        # Last step: Generate button
                        generate_clicked = st.button("🚀 Generate Draft", use_container_width=True, type="primary")
                
                if current_step == total_steps - 1 and generate_clicked:
                    # Validate company profile mandatory fields
                    company = st.session_state.company_profile
                    missing = []
                    if not company["company_name"]: missing.append("Company Name")
                    if not company["industry"]: missing.append("Industry")
                    if not company["region"]: missing.append("Region")
                    if not company["jurisdiction"]: missing.append("Jurisdiction")
                    if missing:
                        st.error(f"❌ Please complete all mandatory Company Profile fields: {', '.join(missing)}.")
                        st.stop()
                    
                    # Validate AI questions
                    question_answers = {}
                    unanswered = []

                    for i, q in enumerate(st.session_state.pending_questions):
                        key = q["key"]
                        unique_key = f"aiq_{i}_{key}"   # ✅ must MATCH render key

                        value = st.session_state.get(unique_key, "")
                        question_answers[key] = value

                        if not value:
                            unanswered.append(q["question"])

                    if unanswered:
                        st.error("❌ Please answer the following questions:")
                        for q in unanswered:
                            st.error(f"  - {q}")
                        st.stop()
                    
                    # Collect all document inputs
                    all_inputs = {}
                    for step in range(len(all_doc_groups)):
                        for field in all_doc_groups[step]["fields"]:
                            key = f"step_{step}_{field['key']}"
                            if key in st.session_state:
                                all_inputs[field['key']] = st.session_state[key]
                    
                    # Convert dates to ISO
                    for key, value in all_inputs.items():
                        if hasattr(value, "isoformat"):
                            all_inputs[key] = value.isoformat()
                    
                    # Merge AI answers
                    all_inputs.update(question_answers)
                    
                    # Generate final draft
                    with st.spinner("🎨 Crafting your document..."):
                        try:
                            gen_resp = requests.post(
                                f"{API_BASE_URL}/documents/generate",
                                json={
                                    "department": department.lower(),
                                    "document_filename": document_filename,
                                    "company_profile": company,
                                    "document_inputs": all_inputs
                                }
                            )
                            result = gen_resp.json()
                            if result.get("status") == "draft_saved":
                                st.success("✅ Draft Generated Successfully!")
                                st.balloons()
                                st.session_state.selected_draft_id = result["draft_id"]
                                # Clear any previous edit states for new draft
                                st.rerun()  # Rerun to fetch and display the draft
                            elif result.get("status") == "questions_required":
                                st.error("Some information is still missing. Please review and try again.")
                            else:
                                st.error("Draft generation failed")
                        except Exception as e:
                            st.error(f"❌ Backend connection error: {e}")
            else:
                st.error("Failed to load document configuration.")
        except Exception as e:
            st.error(f"❌ Backend connection error: {e}")
    else:
        st.info("👈 Please select a document template from the sidebar to begin generating a draft.")
    
    # After generation, if a draft is selected, fetch and display it in this tab
    if st.session_state.selected_draft_id:
        try:
            with st.spinner("Loading draft..."):
                resp = requests.get(f"{API_BASE_URL}/documents/draft/{st.session_state.selected_draft_id}")
            if resp.status_code == 200:
                draft_detail = resp.json()
                render_draft_review(draft_detail, prefix="gen")  # ← prefix added
            else:
                st.error("Failed to load draft.")
        except Exception as e:
            st.error(f"❌ Failed to load draft: {e}")

# ==================== DRAFT LIBRARY TAB ====================
with tab_lib:
    st.subheader("📚 Document Library")
    
    # UI: Add metrics for quick overview
    try:
        response = requests.get(f"{API_BASE_URL}/documents/drafts")
        if response.status_code == 200:
            drafts = response.json()
            if drafts:
                # Calculate metrics
                total_drafts = len(drafts)
                published = sum(1 for d in drafts if d.get('status') == 'published')
                draft_count = total_drafts - published
                
                # Display metrics in columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Drafts", total_drafts)
                with col2:
                    st.metric("Published", published)
                with col3:
                    st.metric("In Progress", draft_count)
                
                st.divider()
                
                search = st.text_input("🔍 Search documents", placeholder="Type to search...", key="lib_search")
                
                unique_docs = {}
                for draft in drafts:
                    name = draft["document_name"]
                    if name not in unique_docs or draft["version"] > unique_docs[name]["version"]:
                        unique_docs[name] = draft
                filtered_drafts = list(unique_docs.values())
                
                if search:
                    filtered_drafts = [d for d in filtered_drafts if search.lower() in d['document_name'].lower()]
                
                if filtered_drafts:
                    for i in range(0, len(filtered_drafts), 2):
                        cols = st.columns(2)
                        for j in range(2):
                            if i + j < len(filtered_drafts):
                                draft = filtered_drafts[i + j]
                                with cols[j]:
                                    with st.container(border=True):
                                        col1, col2 = st.columns([3, 1])
                                        with col1:
                                            st.write(f"**{draft['document_name'][:25]}{'...' if len(draft['document_name']) > 25 else ''}**")
                                            st.caption(f"v{draft.get('version', '1.0')}")
                                        with col2:
                                            if draft['status'] == 'published':
                                                st.success("✅ Published")
                                            else:
                                                st.warning("📝 Draft")
                                        
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            if st.button("👁️ View", key=f"v_{draft['id']}", use_container_width=True):
                                                st.session_state.selected_draft_id = draft["id"]
                                                st.rerun()
                                        with col2:
                                            if st.button("🗑️ Delete", key=f"d_{draft['id']}", use_container_width=True):
                                                with st.spinner("Deleting..."):
                                                    response = requests.delete(f"{API_BASE_URL}/documents/draft/{draft['id']}")

                                                    if response.status_code == 200:
                                                        st.success("Deleted successfully")
                                                 
                                                        if st.session_state.selected_draft_id == draft["id"]:
                                                            st.session_state.selected_draft_id = None
                                                        st.rerun()
                                                    else:
                                                        st.error("Delete failed")
                                                st.rerun()
                else:
                    st.info("No matching documents found")
            else:
                st.info("No documents found in library")
    except Exception as e:
        st.error(f"❌ Failed to load drafts: {e}")
    
    # If a draft is selected (e.g., from clicking View), fetch and display it in this tab
    if st.session_state.selected_draft_id:
        try:
            with st.spinner("Loading draft..."):
                resp = requests.get(f"{API_BASE_URL}/documents/draft/{st.session_state.selected_draft_id}")
            if resp.status_code == 200:
                draft_detail = resp.json()
                render_draft_review(draft_detail, prefix="lib")  # ← prefix added
            else:
                st.error("Failed to load draft.")
        except Exception as e:
            st.error(f"❌ Failed to load draft: {e}")

# ==================== CITERAG LAB TAB ====================
with tab_rag:
    st.subheader("🔎 CiteRAG Knowledge Search")

    # UI: Group filters in a container with border
    with st.container(border=True):
        st.markdown("### Filters")
        col1, col2, col3 = st.columns(3)

        with col1:
            doc_type = st.selectbox(
                "Document Type",
                ["All", "Policy", "Runbook", "Handbook", "Template", "SOP", "FORM"]
            )

        with col2:
            industry = st.radio(
                "Industry",
                ["All", "SaaS"],
                horizontal=True
            )

        with col3:
            from backend.rag.notion_reader import get_all_versions

            try:
                versions = get_all_versions()
            except:
                versions = []

            version_options = ["Latest"] + [str(v) for v in versions]

            selected_version = st.selectbox(
                "Version",
                version_options,
                key="version_filter"
            )

    doc_type_filter = None if doc_type == "All" else doc_type
    industry_filter = None if industry == "All" else industry
    if selected_version == "Latest":
        version_filter = "latest"
    else:
        version_filter = int(selected_version)

    # UI: Tool tabs with better spacing
    tool_tabs = st.tabs(["🔎 Search", "📘 Compare", "📝 Summarize"])

    # ======================================================
    # 🔎 SEARCH TAB
    # ======================================================
    with tool_tabs[0]:
        st.caption("Ask questions about company documents stored in Notion")
        question = st.text_input(
            "Ask a question about company policies or procedures",
            key="rag_question"
        )

        ask_clicked = st.button("Ask", use_container_width=False)

        if ask_clicked:
            if not question:
                st.warning("Please enter a question")
            else:
                with st.spinner("Searching knowledge base..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/documents/rag-query",
                            json={
                                "question": question,
                                "doc_type": doc_type_filter,
                                "industry": industry_filter,
                                "version": version_filter
                            }
                        )
                        if response.status_code != 200:
                            st.error(f"❌ API Error: {response.text}")
                            st.stop()

                        try:
                            result = response.json()
                        except Exception:
                            st.error("❌ Invalid response from backend")
                            st.text(response.text)
                            st.stop()

                        # 🔍 Refined Query
                        st.markdown("### 🔍 Refined Query")
                        st.write(result.get("refined_query", question))

                        # 📌 Answer
                        st.markdown("### 📌 Answer")
                        st.write(result.get("answer", "No answer found"))

                        # 📊 Confidence
                        st.markdown("### 📊 Confidence")

                        confidence_score = result.get("confidence_score", 0)

                        st.markdown(f"**Confidence Score:** {confidence_score}%")
                        st.progress(confidence_score / 100)

                        # 📚 Sources
                        st.markdown("### 📚 Sources")
                        for source in result.get("sources", []):
                            st.write(f"• {source}")

                        # 🔎 Context
                        st.markdown("### 🔎 Retrieved Context")
                        for chunk in result.get("chunks", []):
                            with st.expander(f"{chunk['doc_title']} → {chunk['section']}"):
                                st.write(chunk["text"])
                                st.caption(f"Score: {chunk.get('score', 0):.3f}")
                    except Exception as e:
                        st.error(f"Query failed: {e}")

    # ======================================================
    # 📘 COMPARE TAB (UPDATED)
    # ======================================================
    with tool_tabs[1]:
        st.subheader("Compare Documents")

        # 🔥 Fetch from Notion directly
        try:
            from backend.rag.notion_reader import get_all_document_titles

            available_docs = get_all_document_titles()

        except Exception as e:
            available_docs = []
            st.warning(f"⚠️ Unable to fetch documents from Notion: {e}")

        # 📊 Show count
        st.caption(f"📚 {len(available_docs)} documents available")

        # ---------------- DROPDOWN ----------------
        col1, col2 = st.columns(2)
        with col1:
            doc_a = st.selectbox("Document A", available_docs, key="compare_doc_a_dropdown")
        with col2:
            doc_b = st.selectbox("Document B", available_docs, key="compare_doc_b_dropdown")


        is_valid_search = True

        # ---------------- TOPIC ----------------
        topic = st.text_input("Comparison Topic", key="compare_topic")

        # ---------------- COMPARE BUTTON ----------------
        if st.button("Compare", use_container_width=False, disabled=not is_valid_search):

            if not doc_a or not doc_b:
                st.warning("Please select both documents")

            else:
                with st.spinner("Comparing documents..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/documents/rag-compare",
                            json={
                                "doc_a": doc_a,
                                "doc_b": doc_b,
                                "topic": topic,
                                "version": version_filter
                            }
                        )

                        if response.status_code != 200:
                            st.error(f"❌ API Error: {response.text}")
                            st.stop()

                        try:
                            result = response.json()
                        except Exception:
                            st.error("❌ Invalid response from backend")
                            st.text(response.text)
                            st.stop()

                        st.markdown("### 📌 Comparison")

                        st.markdown(f"**Document A:** {doc_a}")
                        st.markdown(f"**Document B:** {doc_b}")

                        display_topic = topic if topic else "-"
                        st.markdown(f"**Comparision Topic:** {display_topic}")

                        st.divider()

                        st.write(result.get("answer", ""))

                    except Exception as e:
                        st.error(f"Comparison failed: {e}")

    # ======================================================
    # 📝 SUMMARIZE TAB
    # ======================================================
    with tool_tabs[2]:
        st.subheader("Summarize Document")
        from backend.rag.notion_reader import get_all_document_titles

        try:
            available_docs = get_all_document_titles()
        except:
            available_docs = []

        summary_query = st.selectbox(
            "Select document to summarize",
            available_docs,
            key="summary_query"
        )

        if st.button("Summarize", use_container_width=False):
            if not summary_query:
                st.warning("Please select a document")
            else:
                with st.spinner("Generating summary..."):
                    try:
                        # FIX: Changed 'query' to 'content' as per backend expectation
                        response = requests.post(
                            f"{API_BASE_URL}/documents/rag-summarize",
                            json={
                                "query": summary_query,
                                "doc_type": doc_type_filter,
                                "industry": industry_filter,
                                "version": version_filter
                            }
                        )
                        if response.status_code != 200:
                            st.error(f"❌ API Error: {response.text}")
                            st.stop()

                        try:
                            result = response.json()
                        except Exception:
                            st.error("❌ Invalid response from backend")
                            st.text(response.text)
                            st.stop()
                        st.markdown("### 📝 Summary")
                        st.write(result.get("summary", ""))
                    except Exception as e:
                        st.error(f"Summarization failed: {e}")

    st.divider()
    st.subheader("📊 RAG Evaluation")
    if st.button("Run Evaluation", use_container_width=False):
        with st.spinner("Running evaluation... ⏳"):
            response = requests.post(f"{API_BASE_URL}/documents/rag-evaluate")
        if response.status_code == 200:
            result = response.json()
            st.subheader("📋 Detailed Results")
            st.dataframe(result["data"])
            st.subheader("📈 Average Scores")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Faithfulness", f"{result['avg_faithfulness']:.3f}")
            col2.metric("Relevancy", f"{result['avg_relevancy']:.3f}")
            col3.metric("Context Precision", f"{result['avg_context_precision']:.3f}")
            col4.metric("Context Recall", f"{result['avg_context_recall']:.3f}")
        else:
            st.error("Evaluation failed")
            st.write(response.text)

# ==================== STATECASE ASSISTANT TAB ====================
with tab_statecase:

    st.subheader("🤖 StateCase Assistant")
    st.caption("Conversational AI with memory + ticketing")

    # ---------------- SESSION ----------------
    if "session_id" not in st.session_state:
        st.session_state.session_id = "user1"

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ---------------- INPUT ----------------
    user_input = st.text_input("Ask anything...", key="statecase_input")

    col1, col2 = st.columns([1, 5])

    with col1:
        send_clicked = st.button("Send", use_container_width=True)

    # ---------------- API CALL ----------------
    if send_clicked and user_input:

        with st.spinner("Thinking... 🤔"):

            try:
                response = requests.post(
                    f"{API_BASE_URL}/documents/statecase-chat",
                    json={
                        "session_id": st.session_state.session_id,
                        "question": user_input,
                        "doc_type": doc_type_filter,
                        "industry": industry_filter,
                        "version": version_filter
                    }
                )
                
                result = response.json()
                st.write("DEBUG API RESPONSE:", result)

                # save chat
                st.session_state.chat_history.append(("user", user_input))
                st.session_state.chat_history.append((
                    "assistant",
                    {
                        "answer": result["answer"],
                        "sources": result.get("sources", [])
                    }
                ))

                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")

    # ---------------- CHAT DISPLAY ----------------
    st.divider()

    for role, msg in st.session_state.chat_history:

        if role == "user":
            st.markdown(f"🧑 You: {msg}")

        else:
            # ✅ show answer
            st.markdown(f"🤖 Assistant: {msg['answer']}")

            # 🔥 ADD THIS BLOCK (THIS IS MISSING)
            sources = msg.get("sources", [])

            if sources:
                st.markdown("📚 **Sources:**")
                for s in msg["sources"]:
                    st.write(f"- {s}")

    # ---------------- STATUS ----------------
    if st.session_state.chat_history:
        last_response = st.session_state.chat_history[-1][1]

        # ✅ handle dict or string
        if isinstance(last_response, dict):
            text = last_response.get("answer", "")
        else:
            text = last_response

        if "more details" in text.lower():
            st.info("ℹ️ Assistant needs more details")

        if "ticket has been created" in text.lower():
            st.warning("📌 Ticket created in Notion")

    # ---------------- CLEAR CHAT ----------------
    if st.button("🗑 Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

    # ======================================================
    # 📋 MY TICKETS
    # ======================================================
    st.divider()
    st.subheader("📋 My Tickets")

    if st.button("Refresh Tickets", key="refresh_tickets"):

        try:
            url = f"https://api.notion.com/v1/databases/{os.getenv('NOTION_TICKET_DATABASE_ID')}/query"

            headers = {
                "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
                "Notion-Version": "2022-06-28"
            }

            response = requests.post(url, headers=headers)

            if response.status_code == 200:
                data = response.json().get("results", [])

                if not data:
                    st.info("No tickets found")

                for item in data:
                    props = item["properties"]

                    title = props["Title"]["title"][0]["text"]["content"] if props["Title"]["title"] else "No title"
                    status = props["Status"]["select"]["name"] if props["Status"]["select"] else "N/A"
                    priority = props["Priority"]["select"]["name"] if props["Priority"]["select"] else "N/A"

                    with st.container(border=True):
                        st.write(f"📌 **{title}**")
                        st.write(f"Status: {status} | Priority: {priority}")

            else:
                st.error("Failed to fetch tickets")

        except Exception as e:
            st.error(f"Error fetching tickets: {e}")

# -------------------- FOOTER --------------------
st.divider()
col1, col2, col3 = st.columns(3)
with col2:
    st.caption("⚡ DocForge Hub - AI-Powered Intelligent Document Generation Platform")
    st.caption("© 2024 All rights reserved")