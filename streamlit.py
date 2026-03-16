import os
import streamlit as st
import requests
from backend.utils.schema_merger import merge_input_groups
import pandas as pd
from backend.generation.question_label_enhancer import enhance_label
from datetime import datetime, date
import json

API_BASE_URL = "http://127.0.0.1:8000"

# ---------------- UI CONFIG & ENHANCED STYLING ----------------
st.set_page_config(
    page_title="DocForge Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Elegant light theme with extra fixes for checkbox, images, universal text visibility, and cursor
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        background: #f8fafc;
        font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #eef2f6;
        box-shadow: 2px 0 20px rgba(0, 0, 0, 0.02);
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #1e293b !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #eef2f6 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f1f5f9;
        padding: 4px;
        border-radius: 40px;
        border: 1px solid #e2e8f0;
        width: 100%;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1;
        text-align: center;
        border-radius: 30px;
        padding: 8px 20px;
        font-weight: 500;
        color: #64748b;
        transition: all 0.2s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #e2e8f0;
        color: #0f172a;
    }
    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #2563eb !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
        border: 1px solid #e2e8f0;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #2563eb, #3b82f6) !important;
        border-radius: 10px;
    }
    .stProgress {
        margin-bottom: 5px !important;
    }
    .step-container {
        display: flex;
        justify-content: center;
        gap: 30px;
        margin: 10px 0 20px 0;
        padding: 15px;
        background: #f8fafc;
        border-radius: 60px;
        border: 1px solid #eef2f6;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 5px 15px;
        border-radius: 30px;
        transition: all 0.3s ease;
    }
    .step-item.active {
        background: rgba(37, 99, 235, 0.1);
        border: 1px solid rgba(37, 99, 235, 0.3);
    }
    .step-number {
        width: 32px; height: 32px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 600; font-size: 0.9rem;
    }
    .step-number.active   { background: #2563eb; color: white; }
    .step-number.completed { background: #10b981; color: white; }
    .step-number.pending  { background: #e2e8f0; color: #64748b; }
    .step-text { font-size: 0.9rem; font-weight: 500; color: #64748b; }
    .step-text.active { color: #2563eb; }
    .group-card {
        background: #ffffff;
        border: 1px solid #eef2f6;
        border-radius: 20px;
        padding: 25px;
        margin-top: 0;
        margin-bottom: 25px;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
    }
    .group-card:hover {
        border-color: #2563eb40;
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.05);
    }
    .group-header {
        display: flex; align-items: center; gap: 15px;
        margin-bottom: 20px; padding-bottom: 15px;
        border-bottom: 1px solid #eef2f6;
    }
    .group-icon {
        width: 48px; height: 48px;
        background: #f1f5f9;
        border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        color: #2563eb; font-size: 1.6rem;
    }
    .group-title { font-size: 1.2rem; font-weight: 600; color: #0f172a; }
    .group-description { font-size: 0.85rem; color: #64748b; }
    .document-paper {
        background: #ffffff;
        padding: 60px 80px;
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.05);
        font-family: 'Inter', sans-serif;
        line-height: 1.7;
        color: #1e293b;
        max-width: 900px;
        margin: 30px auto;
        border: 1px solid #eef2f6;
    }
    .document-paper h1 {
        font-size: 2.5rem; font-weight: 700;
        color: #0f172a; margin-bottom: 25px; text-align: center;
    }
    .document-paper h2 {
        font-size: 1.6rem; font-weight: 600;
        color: #0f172a; margin-top: 30px; margin-bottom: 15px;
        border-bottom: 2px solid #eef2f6; padding-bottom: 8px;
    }
    .document-paper .stExpander {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    .document-paper .stExpander > div:first-child {
        margin-top: 0 !important;
    }
    /* Remove empty space after expand-all checkbox */
    .stCheckbox {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    .stCheckbox + div {
        margin-top: 0 !important;
    }
    /* Ensure all images in document preview are limited */
    .document-paper img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 20px auto;
    }

    /* Main content text – dark gray, never light */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp p, .stApp li, .stApp span, .stApp div,
    .stApp .stMarkdown, .stApp .stMarkdown p,
    .stApp [data-testid="stMarkdownContainer"] * {
        color: #1e293b !important;
    }

    /* Sidebar text – also dark */
    [data-testid="stSidebar"] * {
        color: #1e293b !important;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label {
        color: #0f172a !important;
        font-weight: 500;
    }

    /* Form labels – ensure visibility */
    .stTextInput label, .stTextArea label, .stSelectbox label,
    .stDateInput label, .stNumberInput label {
        color: #0f172a !important;
        font-weight: 500;
    }

    /* Input text – always black/dark, with visible cursor */
    .stTextInput input, .stTextArea textarea, .stNumberInput input,
    .stDateInput input, input[type="text"], input[type="number"], textarea {
        color: #0f172a !important;
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        caret-color: #2563eb !important;  /* blue cursor for visibility */
    }

    /* Ensure cursor stays visible on focus and active */
    .stTextInput input:focus, .stTextInput input:active,
    .stTextArea textarea:focus, .stTextArea textarea:active,
    .stNumberInput input:focus, .stNumberInput input:active,
    .stDateInput input:focus, .stDateInput input:active {
        caret-color: #2563eb !important;
        color: #0f172a !important;
        background: #ffffff !important;
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
    }

    /* Placeholders – visible but muted */
    ::placeholder {
        color: #64748b !important;
        opacity: 1 !important;
    }

    /* Dropdown options */
    [data-baseweb="popover"] li {
        color: #0f172a !important;
        background: #ffffff !important;
    }
    [data-baseweb="popover"] li:hover {
        background: #f1f5f9 !important;
    }

    /* Progress bar text */
    .stProgress + div small,
    [data-testid="stProgressBarMessage"] {
        color: #334155 !important;
    }

    /* Footer – lighter but still visible */
    .footer p {
        color: #475569 !important;
    }

    /* ---------- DOWNLOAD BUTTON STYLES ---------- */
    .download-button {
        display: inline-block;
        background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
        color: white !important;
        border: none !important;
        border-radius: 30px !important;
        padding: 10px 25px !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        text-decoration: none;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
        text-align: center;
        width: 100%;
        cursor: pointer;
    }
    .download-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 18px rgba(37, 99, 235, 0.3) !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
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

# ---------------- HELPER FUNCTIONS ----------------
def format_date(date_string):
    try:
        date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return date_obj.strftime("%B %d, %Y at %I:%M %p")
    except:
        return date_string

def get_status_badge(status):
    colors = {
        "draft": ("badge-draft", "📝 Draft"),
        "published": ("badge-published", "✅ Published"),
        "archived": ("badge-draft", "📦 Archived")
    }
    badge_class, text = colors.get(status.lower(), ("badge-draft", status))
    return f'<span class="status-badge {badge_class}">{text}</span>'

# def get_icon(icon_name):
#     icon_map = {
#         "keyboard_double_arrow_left": "⬅️",
#         "keyboard_double_arrow_right": "➡️",
#         "double_arrow_right": "➡️",
#         "double_arrow_left": "⬅️",
#         "arrow_right": "➡️",
#         "arrow_left": "⬅️",
#         "document": "📄",
#         "company": "🏢"
#     }

#     return icon_map.get(icon_name, "📄")

def render_field(label, field, key):
    field_type = field["type"]
    if field_type == "text": 
        return st.text_input(label, key=key, placeholder=f"Enter {label.lower()}...")
    elif field_type == "textarea": 
        return st.text_area(label, key=key, height=80, placeholder=f"Enter {label.lower()}...")
    elif field_type == "number": 
        return st.number_input(label, key=key, min_value=0)
    elif field_type == "boolean": 
        return st.checkbox(label, key=key)
    elif field_type == "date": 
        return st.date_input(label, key=key)
    elif field_type == "dropdown": 
        return st.selectbox(label, field.get("options", []), key=key)
    elif field_type == "multiselect": 
        return st.multiselect(label, field.get("options", []), key=key)
    else: 
        return st.text_input(label, key=key, placeholder=f"Enter {label.lower()}...")

def render_company_step():
    """Render the company profile step with a card layout"""
    st.markdown("""
        <div class="group-card">
            <div class="group-header">
                <div class="group-icon">🏢</div>
                <div>
                    <div class="group-title">Company Profile</div>
                    <div class="group-description">Mandatory: Profile details are embedded into the document.</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
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
    """Render a document group step (base or doc) with label enhancement"""
    st.markdown(f"""
        <div class="group-card">
            <div class="group-header">
                <div>
                    <div class="group-title">{group['group_name']}</div>
                    <div class="group-description">{group.get('description', '')}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    fields = group["fields"]
    cols = st.columns(2)
    user_inputs = {}
    validation_errors = []
    for idx, field in enumerate(fields):
        key = field["key"]
        raw_label = field["label"]
        # Apply label enhancer (original logic)
        cache_key = f"enhanced_{doc_name}_{raw_label}"
        if cache_key not in st.session_state:
            st.session_state[cache_key] = enhance_label(raw_label, doc_name)
        label = st.session_state[cache_key]
        if field.get("required"): 
            label = f"{label} *"
        with cols[idx % 2]:
            value = render_field(label, field, f"step_{step_idx}_{key}")
            user_inputs[key] = value
            if field.get("required") and not value:
                validation_errors.append(f"{field['label']} is required.")
    return user_inputs, validation_errors

# ---------------- SIDEBAR (streamlined) ----------------
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <div style='font-size: 2.5rem;'>⚡</div>
            <h1 style='color: #0f172a; font-size: 1.5rem;'>DocForge Hub</h1>
            <p style='color: #64748b; font-size: 0.8rem;'>AI-Powered Document Generation</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.markdown("### 📍 Document")
    departments = [
        "HR", "IT Operations", "Legal", "Marketing", "Finance & Accounting",
        "Engineering", "Quality Assurance", "Security & Compliance",
        "Customer Success", "Product Management"
    ]
    department = st.selectbox("Department", departments, key="sidebar_department")

    try:
        response = requests.get(f"{API_BASE_URL}/documents/list", params={"department": department})
        documents_meta = response.json() if response.status_code == 200 else []
    except:
        documents_meta = []
        st.warning("⚠️ Backend connection failed")

    document_types = sorted(set(doc["internal_type"] for doc in documents_meta))
    selected_type = st.selectbox("Document Type", ["ALL"] + document_types, key="sidebar_doc_type")

    filtered_docs = documents_meta if selected_type == "ALL" else [doc for doc in documents_meta if doc["internal_type"] == selected_type]
    document_filename = st.selectbox("Document Template", [doc["document_name"] for doc in filtered_docs], key="sidebar_document") if filtered_docs else None

# ---------------- MAIN CONTENT ----------------
st.markdown("""
    <div class='welcome-header'>
        <div style='text-align: center; padding: 20px 0;'>
            <h1>⚡ DocForge Hub</h1>
            <p style='color: #64748b;'>Intelligent document generation platform powered by AI</p>
        </div>
    </div>
""", unsafe_allow_html=True)

tabs = st.tabs(["✨ Generate Draft", "📚 Draft Library"])
tab_gen = tabs[0]
tab_lib = tabs[1]

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
            response = requests.post(f"{API_BASE_URL}/documents/preview", 
                                   json={"department": department, "document_filename": document_filename})
            
            if response.status_code == 200:
                doc_config = response.json()
                merged_groups = merge_input_groups(doc_config)
                
                base_groups = [g for g in merged_groups if g.get("source") == "base"]
                doc_groups = [g for g in merged_groups if g.get("source") != "base"]
                
                # --- MERGE DOCUMENT GROUPS INTO LARGER STEPS ---
                all_doc_groups = base_groups + doc_groups
                merged_steps = []          # list of lists of (original_index, group)
                step_size = 3               # combine 3 groups per step – adjust as needed
                for i in range(0, len(all_doc_groups), step_size):
                    step_groups = []
                    for j in range(i, min(i+step_size, len(all_doc_groups))):
                        step_groups.append((j, all_doc_groups[j]))
                    merged_steps.append(step_groups)
                doc_step_count = len(merged_steps)
                total_steps = 1 + doc_step_count + 1   # company + merged doc steps + AI questions
                current_step = st.session_state.current_step
                
                # Progress bar
                st.progress((current_step + 1) / total_steps, text=f"Step {current_step + 1} of {total_steps}")
                
                # Step indicators
                step_names = ["Company Profile"] + [f"Section {i+1}" for i in range(doc_step_count)] + ["Document Specific Questions"]
                st.markdown('<div class="step-container">', unsafe_allow_html=True)
                cols = st.columns(total_steps)
                for i, col in enumerate(cols):
                    with col:
                        if i == current_step:
                            number_class = "active"
                            text_class = "active"
                        elif i < current_step:
                            number_class = "completed"
                            text_class = "pending"
                        else:
                            number_class = "pending"
                            text_class = "pending"
                        st.markdown(f"""
                            <div class='step-item {text_class}'>
                                <div class='step-number {number_class}'>{i+1}</div>
                                <div class='step-text {text_class}'>{step_names[i]}</div>
                            </div>
                        """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Render current step
                validation_errors = []
                if current_step == 0:
                    # Company profile step
                    render_company_step()
                elif current_step <= doc_step_count:
                    # Document step (index current_step - 1 in merged_steps)
                    step_groups = merged_steps[current_step - 1]
                    for (orig_idx, group) in step_groups:
                        if 'icon' not in group:
                            group['icon'] = "📄"
                        if 'description' not in group:
                            group['description'] = f"{doc_config['document_name']} details"
                        user_inputs, errs = render_document_step(orig_idx, group, doc_config['document_name'])
                        validation_errors.extend(errs)
                        # Save inputs to session state
                        for key, value in user_inputs.items():
                            st.session_state.form_data[f"{orig_idx}_{key}"] = value
                else:
                    # Last step: AI Questions
                    st.markdown("### Additional Governance Information")
                    # Generate AI questions if not already done
                    if not st.session_state.pending_questions and not st.session_state.questions_generated:
                        # Collect all document inputs so far
                        all_inputs = {}
                        for step in range(len(all_doc_groups)):
                            for field in all_doc_groups[step]["fields"]:
                                key = f"step_{step}_{field['key']}"
                                if key in st.session_state:
                                    all_inputs[field['key']] = st.session_state[key]
                        # Prepare safe inputs for API
                        safe_inputs = {}
                        for key, value in all_inputs.items():
                            if hasattr(value, "isoformat"):
                                safe_inputs[key] = value.isoformat()
                            else:
                                safe_inputs[key] = value
                        # Call generate-questions
                        questions_response = requests.post(
                            f"{API_BASE_URL}/documents/generate-questions",
                            json={
                                "department": department.lower(),
                                "document_filename": document_filename,
                                "company_profile": {
                                    "company_name": st.session_state.company_profile.get("company_name", ""),
                                    "industry": st.session_state.company_profile.get("industry", ""),
                                    "employee_count": st.session_state.company_profile.get("employee_count", 0),
                                    "regions": [st.session_state.company_profile.get("region", "")],
                                    "compliance_frameworks": [st.session_state.company_profile.get("compliance", "")],
                                    "default_jurisdiction": st.session_state.company_profile.get("jurisdiction", "")
                                },
                                "document_inputs": safe_inputs
                            }
                        )
                        if questions_response.status_code == 200:
                            st.session_state.pending_questions = questions_response.json().get("questions", [])
                            st.session_state.questions_generated = True
                    # Display AI questions
                    for q in st.session_state.pending_questions:
                        key = q["key"]
                        question_text = q["question"]
                        q_type = q.get("type", "text")
                        unique_key = f"aiq_{department}_{document_filename}_{key}"
                        if q_type == "textarea":
                            st.text_area(question_text, key=unique_key)
                        else:
                            st.text_input(question_text, key=unique_key)
                
                # Navigation buttons
                nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
                with nav_col1:
                    if current_step > 0:
                        if st.button("◀ Previous", use_container_width=True):
                            st.session_state.current_step -= 1
                            st.rerun()
                with nav_col3:
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
                
                # Spinner appears after the button – we can't move it, but we can add a blank column to balance
                if current_step == total_steps - 1 and generate_clicked:
                    # Validate company profile mandatory fields
                    company = st.session_state.company_profile
                    if not all([company["company_name"], company["industry"], company["region"], company["jurisdiction"]]):
                        st.error("❌ Please complete all mandatory Company Profile fields (Name, Industry, Region, Jurisdiction).")
                        st.stop()
                    # Validate AI questions
                    question_answers = {}
                    for q in st.session_state.pending_questions:
                        key = q["key"]
                        unique_key = f"aiq_{department}_{document_filename}_{key}"
                        value = st.session_state.get(unique_key, "")
                        question_answers[key] = value
                        if not value:
                            st.error(f"Please answer: {q['question']}")
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
                                st.session_state.current_step = 0
                                st.rerun()
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

# ==================== DRAFT LIBRARY TAB ====================
with tab_lib:
    st.markdown("### 📚 Document Library")
    
    search = st.text_input("🔍 Search", placeholder="Type to search...", key="lib_search")
    
    try:
        response = requests.get(f"{API_BASE_URL}/documents/drafts")
        if response.status_code == 200:
            drafts = response.json()
            if drafts:
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
                                    st.markdown(f"""
                                        <div class="draft-card">
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                                <div>
                                                    <strong style="color: #0f172a;">{draft['document_name'][:25]}{'...' if len(draft['document_name']) > 25 else ''}</strong>
                                                    <div style="font-size: 0.8rem; color: #64748b;">v{draft.get('version', '1.0')}</div>
                                                </div>
                                                {get_status_badge(draft['status'])}
                                            </div>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("👁️ View", key=f"v_{draft['id']}", use_container_width=True):
                                            st.session_state.selected_draft_id = draft["id"]
                                            st.rerun()
                                    with col2:
                                        if st.button("🗑️", key=f"d_{draft['id']}", use_container_width=True):
                                            requests.delete(f"{API_BASE_URL}/documents/draft/{draft['id']}")
                                            st.rerun()
                else:
                    st.info("No matching documents found")
            else:
                st.info("No documents found in library")
    except Exception as e:
        st.error(f"❌ Failed to load drafts: {e}")

# ==================== DOCUMENT REVIEW & PREVIEW (always visible) ====================
if st.session_state.selected_draft_id:
    st.markdown("<hr style='margin: 30px 0; border-color: #eef2f6;'>", unsafe_allow_html=True)
    
    try:
        resp = requests.get(f"{API_BASE_URL}/documents/draft/{st.session_state.selected_draft_id}")
        if resp.status_code == 200:
            draft_detail = resp.json()
            
            # ----- Section Review & Approval (original logic) -----
            st.subheader("Section Review & Approval")
            total_sections = len(draft_detail["sections"])
            approved_sections = sum(1 for s in draft_detail["sections"] if s.get("status") == "approved")
            progress_ratio = approved_sections / total_sections if total_sections else 0
            st.markdown(f"**{approved_sections} of {total_sections} Sections Confirmed**")
            st.progress(progress_ratio)
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
                
                st.markdown(f"## {section_name}")
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
                            # Try URL first
                            if diagram_url:
                                # If URL is already absolute, use it directly
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
                    st.markdown(paragraph_text)
                
                # Action row (Edit, Confirm, Regenerate)
                action_col1, action_col2, action_col3 = st.columns([1,1,2])
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
                                params={"draft_id": st.session_state.selected_draft_id, "section_name": section_name}
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
                        feedback = st.text_input("Improvement Note", key=f"feedback_{section_name}")
                        if st.button("🔄 Regenerate", key=f"regen_{section_name}"):
                            regen_response = requests.post(
                                f"{API_BASE_URL}/documents/regenerate-section",
                                params={"draft_id": st.session_state.selected_draft_id, "section_name": section_name, "improvement_note": feedback}
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
                                text_key = f"edit_content_{draft_detail['id']}_{section_name}"
                                if text_key in st.session_state:
                                    del st.session_state[text_key]
                                st.rerun()
                            else:
                                st.error(save_response.text)
                    st.divider()
            
            # ----- Export buttons (only DOCX kept, now a direct download link) -----
            st.subheader("Final Document Export")
            col1, col2, col3 = st.columns([1, 1, 3])
            if all_approved:
                with col1:
                    st.markdown(
                        f'<a href="{API_BASE_URL}/documents/export/{st.session_state.selected_draft_id}/docx" target="_blank" class="download-button">📥 Download DOCX</a>',
                        unsafe_allow_html=True
                    )
            
            # ----- Full Document Preview (enhanced with expanders) -----
            if all_approved:
                st.divider()
                st.subheader("Full Document Preview")
                expand_all = st.checkbox("Expand all sections", value=False)
    
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
                #----------------Publish doc to notion-------------------
                st.divider()
                st.subheader("Publish Document")
                col1, col2 = st.columns([1,3])
                with col1:
                    if st.button("Publish to Notion", use_container_width=True):
                        with st.spinner("Publishing document to Notion..."):
                            publish_response = requests.post(
                                f"{API_BASE_URL}/documents/publish-notion/{st.session_state.selected_draft_id}"
                            )
                        if publish_response.status_code == 200:
                            st.success("Document successfully published to Notion 🎉")
                        else:
                            st.error("Failed to publish document to Notion")
    except Exception as e:
        st.error(f"❌ Failed to load draft: {e}")

# ---------------- FOOTER ----------------
st.markdown("""
    <div class="footer">
        <p>⚡ DocForge Hub - AI-Powered Intelligent Document Generation Platform</p>
        <p style='font-size: 0.7rem; margin-top: 5px;'>© 2024 All rights reserved</p>
    </div>
""", unsafe_allow_html=True)