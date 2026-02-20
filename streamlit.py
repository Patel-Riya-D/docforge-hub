import streamlit as st
import requests
from backend.utils.schema_merger import merge_input_groups

API_BASE_URL = "http://127.0.0.1:8000"

# ---------------- UI CONFIG & ENHANCED STYLING ----------------
st.set_page_config(
    page_title="DocForge Hub",
    page_icon="📄",
    layout="wide"
)

# Advanced CSS for SaaS Tabs and Professional Document Preview
st.markdown("""
    <style>
    /* 1. Global Background */
    .stApp { background-color: #fcfcfc; }

    /* 2. Enhanced Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #f1f3f5;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 25px;
        font-weight: 600;
        color: #495057;
        border: none;
        transition: all 0.3s;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #ff4b4b !important;
        border-bottom: 3px solid #ff4b4b !important;
        box-shadow: 0 -4px 10px rgba(0,0,0,0.05);
    }

    /* 3. Professional Document Paper UI */
    .document-paper {
        background-color: white;
        padding: 50px 80px;
        border-radius: 4px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        font-family: 'Georgia', 'Times New Roman', serif;
        line-height: 1.7;
        color: #2c3e50;
        max-width: 850px;
        margin: 30px auto;
        border: 1px solid #e0e0e0;
    }
    .document-paper h1, .document-paper h2 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #1a1a1a;
        margin-bottom: 20px;
    }
    .document-paper hr { border-top: 1px solid #eee; margin: 30px 0; }

    /* 4. Action Bar Toolbar */
    .preview-toolbar {
        background-color: white;
        padding: 12px 20px;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        margin-bottom: 10px;
    }
    
    /* 5. Library Cards */
    .draft-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #eee;
        margin-bottom: 12px;
        transition: transform 0.2s;
    }
    .draft-card:hover { border-color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

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
    if field_type == "text": return st.text_input(label, key=key)
    elif field_type == "textarea": return st.text_area(label, key=key, height=100)
    elif field_type == "number": return st.number_input(label, key=key)
    elif field_type == "boolean": return st.checkbox(label, key=key)
    elif field_type == "date": return st.date_input(label, key=key)
    elif field_type == "dropdown": return st.selectbox(label, field.get("options", []), key=key)
    elif field_type == "multiselect": return st.multiselect(label, field.get("options", []), key=key)
    else: return st.text_input(label, key=key)

# ---------------- DYNAMIC FORM ----------------
def render_dynamic_form(base_groups, doc_groups, document_name):
    user_inputs = {}
    validation_errors = []
    
    st.markdown(f"### ⚙️ Configuration: {document_name}")
    
    if base_groups:
        with st.expander("📋 1. General Information", expanded=True):
            for group in base_groups:
                for field in group["fields"]:
                    key, label = field["key"], field["label"]
                    if field.get("required"): label += " *"
                    value = render_field(label, field, key)
                    user_inputs[key] = value
                    if field.get("required") and not value:
                        validation_errors.append(f"{field['label']} is required.")

    if doc_groups:
        with st.expander(f"📄 2. {document_name} Details", expanded=True):
            for group in doc_groups:
                st.markdown(f"**{group['group_name']}**")
                for field in group["fields"]:
                    key, label = field["key"], field["label"]
                    if field.get("required"): label += " *"
                    value = render_field(label, field, key)
                    user_inputs[key] = value
                    if field.get("required") and not value:
                        validation_errors.append(f"{field['label']} is required.")
    return user_inputs, validation_errors

# ---------------- SIDEBAR: SELECTION & MANDATORY PROFILE ----------------
with st.sidebar:
    st.title("🛠️ DocForge Hub")
    st.caption("Generate, Review & Publish")
    st.divider()
    
    st.subheader("📍 Document Selection")
    departments = ["HR", "IT Operations", "Legal", "Marketing", "Finance & Accounting", "Engineering", "Quality Assurance", "Security & Compliance", "Customer Success", "Product Management"]
    department = st.selectbox("Department", departments)

    response = requests.get(f"{API_BASE_URL}/documents/list", params={"department": department})
    documents_meta = response.json() if response.status_code == 200 else []

    document_types = sorted(set(doc["internal_type"] for doc in documents_meta))
    selected_type = st.selectbox("Document Type", ["ALL"] + document_types)

    filtered_docs = documents_meta if selected_type == "ALL" else [doc for doc in documents_meta if doc["internal_type"] == selected_type]
    document_filename = st.selectbox("Document", [doc["document_name"] for doc in filtered_docs]) if filtered_docs else None

    st.divider()
    st.subheader("🏢 Company Profile")
    st.info("Mandatory: Profile details are embedded into the document.")
    company_name = st.text_input("Company Name *")
    industry = st.text_input("Industry *")
    employee_count = st.number_input("Employee Count", min_value=1)
    region = st.text_input("Operating Region *")
    compliance = st.text_input("Compliance Framework")
    jurisdiction = st.text_input("Jurisdiction *")

# ---------------- MAIN APP TABS ----------------
tab_gen, tab_lib = st.tabs(["✨ Generate Draft", "📚 Draft Library"])

with tab_gen:
    if document_filename:
        response = requests.post(f"{API_BASE_URL}/documents/preview", json={"department": department, "document_filename": document_filename})
        
        if response.status_code == 200:
            doc_config = response.json()
            merged_groups = merge_input_groups(doc_config)
            
            base_groups = [g for g in merged_groups if g.get("source") == "base"]
            doc_groups = [g for g in merged_groups if g.get("source") != "base"]

            user_inputs, validation_errors = render_dynamic_form(base_groups, doc_groups, doc_config["document_name"])

            st.divider()
            if st.button("Generate Draft", use_container_width=True, type="primary"):
                # MANDATORY PROFILE VALIDATION
                if not all([company_name, industry, region, jurisdiction]):
                    st.error("❌ Action Required: Please complete all mandatory Company Profile fields in the sidebar.")
                elif validation_errors:
                    for err in validation_errors: st.error(f"❌ {err}")
                else:
                    # Logic for ISO format and API Post
                    for key, value in user_inputs.items():
                        if hasattr(value, "isoformat"): user_inputs[key] = value.isoformat()
                    
                    with st.spinner("Writing document content..."):
                        gen_resp = requests.post(f"{API_BASE_URL}/documents/generate", json={
                            "department": department.lower(),
                            "document_filename": document_filename,
                            "company_profile": {
                                "company_name": company_name, "industry": industry, "employee_count": employee_count,
                                "regions": [region], "compliance_frameworks": [compliance], "default_jurisdiction": jurisdiction
                            },
                            "document_inputs": user_inputs
                        })
                        if gen_resp.status_code == 200:
                            st.success("Draft Generated Successfully")
                            st.session_state.selected_draft_id = gen_resp.json()["draft_id"]
                            st.rerun()
        else:
            st.error("Failed to load document configuration.")
    else:
        st.info("👈 Please select a document template from the sidebar.")

with tab_lib:
    response = requests.get(f"{API_BASE_URL}/documents/drafts")
    if response.status_code == 200:
        drafts = response.json()
        if drafts:
            # Latest draft logic
            unique_docs = {}

            for draft in drafts:
                name = draft["document_name"]

                if name not in unique_docs:
                    unique_docs[name] = draft
                else:
                    # Keep the latest version
                    if draft["version"] > unique_docs[name]["version"]:
                        unique_docs[name] = draft
            
            for draft in unique_docs.values():
                st.markdown(f"""<div class="draft-card">""", unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns([4, 2, 1, 1])
                with c1:
                    st.markdown(f"**{draft['document_name']}**")
                    # st.caption(f"v{draft['version']} • Created {draft['created_at'][:10]}")
                with c2:
                    st.info(f"Status: {draft['status']}")
                with c3:
                    if st.button("View", key=f"v_{draft['id']}", use_container_width=True):
                        st.session_state.selected_draft_id = draft["id"]
                        st.rerun()
                with c4:
                    if st.button("🗑️", key=f"d_{draft['id']}", use_container_width=True):
                        requests.delete(f"{API_BASE_URL}/documents/draft/{draft['id']}")
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No drafts found in the library.")

# ---------------- PROFESSIONAL DOCUMENT PREVIEW ----------------
if st.session_state.selected_draft_id:
    st.divider()
    resp = requests.get(f"{API_BASE_URL}/documents/draft/{st.session_state.selected_draft_id}")
    if resp.status_code == 200:
        draft_detail = resp.json()
        
        # Action Toolbar
        st.markdown(f"""
            <div class="preview-toolbar">
                <span style="font-weight:bold; font-size:1.1rem; color:#1f2937;">📄 {draft_detail['document_name']}</span>
            </div>
            """, unsafe_allow_html=True)
        
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1,1,1,4])
        with btn_col1:
            if st.button("📥 PDF", use_container_width=True):
                st.markdown(f'<a href="{API_BASE_URL}/documents/export/{st.session_state.selected_draft_id}/pdf" target="_blank">Download PDF</a>', unsafe_allow_html=True)
        with btn_col2:
            if st.button("📥 DOCX", use_container_width=True):
                st.markdown(f'<a href="{API_BASE_URL}/documents/export/{st.session_state.selected_draft_id}/docx" target="_blank">Download DOCX</a>', unsafe_allow_html=True)
        with btn_col3:
            if st.button("✖️ Close", use_container_width=True):
                st.session_state.selected_draft_id = None
                st.rerun()

        # Render Content into Paper Container
        full_text = ""
        for section in draft_detail["sections"]:
            full_text += f"## {section['section_name']}\n{section['content']}\n\n"
        
        st.markdown('<div class="document-paper">', unsafe_allow_html=True)
        st.markdown(f"<h1>{draft_detail['document_name']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>Company: {company_name if company_name else 'N/A'}</p>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(full_text)
        st.markdown('</div>', unsafe_allow_html=True)