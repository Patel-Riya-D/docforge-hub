import streamlit as st
from datetime import datetime, date
import random

# ---------------- UI CONFIG & ENHANCED STYLING ----------------
st.set_page_config(
    page_title="DocForge Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Advanced CSS with modern design system
st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Main content area with glass morphism effect */
    .main > div {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(10px);
        border-radius: 30px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.2);
        border: 1px solid rgba(255,255,255,0.5);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #fff;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #fff !important;
    }
    
    /* Modern Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background: transparent;
        padding: 10px 20px;
        border-bottom: 2px solid rgba(0,0,0,0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background: transparent;
        border-radius: 25px;
        padding: 10px 30px;
        font-weight: 600;
        color: #666;
        border: none;
        transition: all 0.3s ease;
        font-size: 1rem;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(102, 126, 234, 0.1);
        color: #667eea;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        box-shadow: 0 10px 20px -5px rgba(102, 126, 234, 0.4);
    }
    
    /* Progress Bar Styling */
    .progress-container {
        background: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
    }
    
    .progress-steps {
        display: flex;
        justify-content: space-between;
        margin: 20px 0;
        position: relative;
    }
    
    .step {
        flex: 1;
        text-align: center;
        position: relative;
    }
    
    .step-number {
        width: 35px;
        height: 35px;
        background: #e2e8f0;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 10px;
        font-weight: 600;
        color: #666;
        transition: all 0.3s ease;
    }
    
    .step.active .step-number {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    .step.completed .step-number {
        background: #10b981;
        color: white;
    }
    
    .step-title {
        font-size: 0.85rem;
        color: #666;
        font-weight: 500;
    }
    
    .step.active .step-title {
        color: #667eea;
        font-weight: 600;
    }
    
    /* Group Cards */
    .group-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .group-card:hover {
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        border-color: #667eea;
    }
    
    .group-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #f0f0f0;
    }
    
    .group-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.2rem;
    }
    
    .group-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1a2e;
    }
    
    .group-description {
        font-size: 0.85rem;
        color: #718096;
    }
    
    /* Professional Document Paper */
    .document-paper {
        background: white;
        padding: 60px 80px;
        border-radius: 20px;
        box-shadow: 0 30px 60px -20px rgba(0,0,0,0.3);
        font-family: 'Playfair Display', serif;
        line-height: 1.8;
        color: #2d3748;
        max-width: 900px;
        margin: 30px auto;
        border: 1px solid rgba(255,255,255,0.3);
        position: relative;
    }
    
    .document-paper::before {
        content: '';
        position: absolute;
        top: 20px;
        left: 20px;
        right: 20px;
        bottom: 20px;
        border: 2px solid #f0f0f0;
        border-radius: 15px;
        pointer-events: none;
    }
    
    .document-paper h1 {
        font-family: 'Inter', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 30px;
        text-align: center;
        letter-spacing: -0.5px;
    }
    
    .document-paper h2 {
        font-family: 'Inter', sans-serif;
        font-size: 1.8rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-top: 40px;
        margin-bottom: 20px;
        border-bottom: 3px solid #667eea;
        padding-bottom: 10px;
    }
    
    /* Form Inputs - Compact for many questions */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input {
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        padding: 8px 12px !important;
        font-size: 0.95rem !important;
        min-height: 38px !important;
    }
    
    /* Library Cards */
    .draft-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
        border: 1px solid #e2e8f0;
        position: relative;
    }
    
    .draft-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.1);
        border-color: #667eea;
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .badge-draft {
        background: #fff3cd;
        color: #856404;
    }
    
    .badge-published {
        background: #d4edda;
        color: #155724;
    }
    
    /* Action Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Section divider */
    .section-divider {
        margin: 30px 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
    }
    
    /* Welcome Header */
    .welcome-header {
        text-align: center;
        padding: 20px 0;
        margin-bottom: 20px;
    }
    
    .welcome-header h1 {
        font-size: 2.5rem;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .welcome-header p {
        color: #666;
        font-size: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- MOCK DATA FOR DOCUMENT INFORMATION (Base Groups) ----------------
DOCUMENT_INFO_GROUPS = [
    {
        "group_name": "Document Information",
        "icon": "📋",
        "description": "Basic document details and metadata",
        "fields": [
            {"key": "doc_title", "label": "Document Title", "type": "text", "required": True},
            {"key": "doc_owner", "label": "Document Owner", "type": "text", "required": True},
            {"key": "department", "label": "Department", "type": "dropdown", "required": True, 
             "options": ["HR", "Engineering", "Marketing", "Legal", "Finance"]},
            {"key": "effective_date", "label": "Effective Date", "type": "date", "required": True},
            {"key": "review_date", "label": "Review Date", "type": "date", "required": True},
            {"key": "version", "label": "Version", "type": "text", "required": False}
        ]
    }
]

# ---------------- MOCK DATA FOR DOCUMENT TYPE GROUPS (e.g., Policy General) ----------------
POLICY_TYPE_GROUPS = [
    {
        "group_name": "Policy Information",
        "icon": "📌",
        "description": "General policy information applicable to all policies",
        "fields": [
            {"key": "policy_purpose", "label": "Policy Purpose", "type": "textarea", "required": True},
            {"key": "policy_scope", "label": "Scope", "type": "textarea", "required": True},
            {"key": "policy_objectives", "label": "Objectives", "type": "textarea", "required": True},
            {"key": "applicable_to", "label": "Applicable To", "type": "multiselect", "required": True,
             "options": ["All Employees", "Management", "HR Team", "IT Team", "Sales Team"]},
            {"key": "policy_category", "label": "Policy Category", "type": "dropdown", "required": True,
             "options": ["HR Policy", "IT Policy", "Security Policy", "Compliance Policy"]},
            {"key": "review_cycle", "label": "Review Cycle", "type": "dropdown", "required": True,
             "options": ["Monthly", "Quarterly", "Annually", "Bi-Annually"]}
        ]
    }
]

CONTRACT_TYPE_GROUPS = [
    {
        "group_name": "Contract Information",
        "icon": "📑",
        "description": "General contract information applicable to all contracts",
        "fields": [
            {"key": "contract_type", "label": "Contract Type", "type": "dropdown", "required": True,
             "options": ["Employment", "Service", "NDA", "Partnership"]},
            {"key": "party_a", "label": "Party A (First Party)", "type": "text", "required": True},
            {"key": "party_b", "label": "Party B (Second Party)", "type": "text", "required": True},
            {"key": "contract_value", "label": "Contract Value", "type": "number", "required": False},
            {"key": "currency", "label": "Currency", "type": "dropdown", "required": False,
             "options": ["USD", "EUR", "GBP", "INR"]},
            {"key": "governing_law", "label": "Governing Law", "type": "text", "required": True}
        ]
    }
]

# ---------------- MOCK DATA FOR DOCUMENT SPECIFIC GROUPS ----------------
# Remote Work Policy (specific document)
REMOTE_WORK_SPECIFIC_GROUPS = [
    {
        "group_name": "Remote Work Specifics",
        "icon": "🏠",
        "description": "Specific details for remote work policy",
        "fields": [
            {"key": "eligible_positions", "label": "Eligible Positions", "type": "multiselect", "required": True,
             "options": ["Full-time", "Part-time", "Contractors", "Interns"]},
            {"key": "probation_period", "label": "Probation Period Required", "type": "boolean", "required": True},
            {"key": "minimum_tenure", "label": "Minimum Tenure (months)", "type": "number", "required": True},
            {"key": "work_schedule", "label": "Work Schedule", "type": "dropdown", "required": True,
             "options": ["Flexible", "Fixed Hours", "Core Hours Only"]},
            {"key": "remote_days_per_week", "label": "Remote Days Per Week", "type": "number", "required": True},
            {"key": "office_days_required", "label": "Office Days Required", "type": "text", "required": True},
            {"key": "company_equipment", "label": "Company Provided Equipment", "type": "textarea", "required": True}
        ]
    }
]

# Employee Handbook Specific
EMPLOYEE_HANDBOOK_SPECIFIC_GROUPS = [
    {
        "group_name": "Handbook Specifics",
        "icon": "📘",
        "description": "Specific details for employee handbook",
        "fields": [
            {"key": "handbook_purpose", "label": "Handbook Purpose", "type": "textarea", "required": True},
            {"key": "company_values", "label": "Company Values", "type": "textarea", "required": True},
            {"key": "work_hours", "label": "Work Hours", "type": "text", "required": True},
            {"key": "leave_policy", "label": "Leave Policy Summary", "type": "textarea", "required": True},
            {"key": "dress_code", "label": "Dress Code", "type": "dropdown", "required": True,
             "options": ["Formal", "Business Casual", "Casual", "None"]},
            {"key": "probation_period", "label": "Probation Period (months)", "type": "number", "required": True},
            {"key": "notice_period", "label": "Notice Period (days)", "type": "number", "required": True}
        ]
    }
]

# Employment Contract Specific
EMPLOYMENT_CONTRACT_SPECIFIC_GROUPS = [
    {
        "group_name": "Employment Specifics",
        "icon": "🤝",
        "description": "Specific details for employment contract",
        "fields": [
            {"key": "position_title", "label": "Position Title", "type": "text", "required": True},
            {"key": "employment_type", "label": "Employment Type", "type": "dropdown", "required": True,
             "options": ["Full-time", "Part-time", "Fixed-term", "Probation"]},
            {"key": "start_date", "label": "Start Date", "type": "date", "required": True},
            {"key": "base_salary", "label": "Base Salary", "type": "number", "required": True},
            {"key": "bonus_eligible", "label": "Bonus Eligible", "type": "boolean", "required": True},
            {"key": "benefits", "label": "Benefits", "type": "multiselect", "required": False,
             "options": ["Health Insurance", "401k", "Stock Options", "Paid Time Off"]},
            {"key": "reporting_manager", "label": "Reporting Manager", "type": "text", "required": True}
        ]
    }
]

# ---------------- MOCK DATA FOR DOCUMENTS MAPPING ----------------
# Structure: Base (Document Info) -> Type (Policy/Contract general) -> Specific (Document specific)
DOCUMENT_GROUPS_MAPPING = {
    "Employee Handbook": {
        "type": "Policy",
        "groups": [
            DOCUMENT_INFO_GROUPS[0],  # Document Information
            POLICY_TYPE_GROUPS[0],     # Policy Type Information
            EMPLOYEE_HANDBOOK_SPECIFIC_GROUPS[0]  # Handbook Specific
        ]
    },
    "Remote Work Policy": {
        "type": "Policy",
        "groups": [
            DOCUMENT_INFO_GROUPS[0],    # Document Information
            POLICY_TYPE_GROUPS[0],       # Policy Type Information
            REMOTE_WORK_SPECIFIC_GROUPS[0]  # Remote Work Specific
        ]
    },
    "Employment Contract": {
        "type": "Contract",
        "groups": [
            DOCUMENT_INFO_GROUPS[0],    # Document Information
            CONTRACT_TYPE_GROUPS[0],     # Contract Type Information
            EMPLOYMENT_CONTRACT_SPECIFIC_GROUPS[0]  # Employment Specific
        ]
    }
}

MOCK_DEPARTMENTS = ["Human Resources", "Engineering", "Marketing", "Legal", "Finance"]
MOCK_DOCUMENTS = [
    {"name": "Employee Handbook", "type": "Policy", "department": "Human Resources"},
    {"name": "Remote Work Policy", "type": "Policy", "department": "Human Resources"},
    {"name": "Employment Contract", "type": "Contract", "department": "Human Resources"},
]

# ---------------- MOCK DRAFTS ----------------
MOCK_DRAFTS = [
    {"id": 1, "name": "Employee Handbook 2024", "status": "draft", "version": "2.0", 
     "created": "2024-01-15", "department": "HR"},
    {"id": 2, "name": "Remote Work Policy v2", "status": "published", "version": "1.0", 
     "created": "2024-02-01", "department": "HR"},
    {"id": 3, "name": "Employment Contract - John Doe", "status": "draft", "version": "1.5", 
     "created": "2024-02-10", "department": "HR"},
]

# ---------------- SESSION STATE ----------------
if "selected_draft_id" not in st.session_state:
    st.session_state.selected_draft_id = None
if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "form_data" not in st.session_state:
    st.session_state.form_data = {}
if "company_profile" not in st.session_state:
    st.session_state.company_profile = {
        "company_name": "Acme Corporation",
        "industry": "Technology",
        "employee_count": 500,
        "region": "North America",
        "jurisdiction": "Delaware, USA"
    }
if "generated_docs" not in st.session_state:
    st.session_state.generated_docs = []

# ---------------- HELPER FUNCTIONS ----------------
def format_date(date_string):
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        return date_obj.strftime("%B %d, %Y")
    except:
        return date_string

def get_status_badge(status):
    colors = {
        "draft": ("badge-draft", "📝 Draft"),
        "published": ("badge-published", "✅ Published")
    }
    badge_class, text = colors.get(status, ("badge-draft", status))
    return f'<span class="status-badge {badge_class}">{text}</span>'

def render_field(field, key_prefix=""):
    field_type = field["type"]
    label = field["label"]
    key = f"{key_prefix}_{field['key']}"
    required = field.get("required", False)
    options = field.get("options", [])
    
    if required:
        label = f"{label} *"
    
    if field_type == "text":
        return st.text_input(label, key=key, placeholder=f"Enter {label.lower()}")
    elif field_type == "textarea":
        return st.text_area(label, key=key, height=80, placeholder=f"Enter {label.lower()}")
    elif field_type == "number":
        return st.number_input(label, key=key, min_value=0)
    elif field_type == "date":
        return st.date_input(label, key=key, value=date.today())
    elif field_type == "dropdown":
        return st.selectbox(label, options, key=key)
    elif field_type == "multiselect":
        return st.multiselect(label, options, key=key)
    elif field_type == "boolean":
        return st.checkbox(label, key=key)
    return st.text_input(label, key=key)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <div style='font-size: 2.5rem;'>⚡</div>
            <h1 style='color: white; font-size: 1.5rem;'>DocForge Hub</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📍 Document")
    department = st.selectbox("Department", MOCK_DEPARTMENTS, key="sidebar_dept")
    
    dept_docs = [doc for doc in MOCK_DOCUMENTS if doc["department"] == department]
    doc_names = [doc["name"] for doc in dept_docs]
    selected_doc = st.selectbox("Template", doc_names, key="sidebar_doc") if doc_names else None
    
    if selected_doc:
        doc_type = next((doc["type"] for doc in MOCK_DOCUMENTS if doc["name"] == selected_doc), "Unknown")
        st.caption(f"Type: {doc_type}")
    
    st.markdown("### 🏢 Company")
    company_name = st.text_input("Company", value=st.session_state.company_profile["company_name"])
    industry = st.text_input("Industry", value=st.session_state.company_profile["industry"])
    region = st.text_input("Region", value=st.session_state.company_profile["region"])

# ---------------- MAIN CONTENT ----------------
st.markdown("""
    <div class='welcome-header'>
        <h1>⚡ Document Forge</h1>
        <p>Intelligent document generation platform</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["✨ Generate", "📚 Library"])

with tab1:
    if selected_doc:
        # Get document configuration
        doc_config = DOCUMENT_GROUPS_MAPPING.get(selected_doc)
        
        if doc_config:
            all_groups = doc_config["groups"]
            total_steps = len(all_groups)
            current_step = st.session_state.current_step
            
            # Progress bar
            progress = (current_step + 1) / total_steps
            st.progress(progress, text=f"Step {current_step + 1} of {total_steps}")
            
            # Step indicators
            step_names = ["Document Info", f"{doc_config['type']} Info", "Specific Details"]
            cols = st.columns(3)
            for i, col in enumerate(cols):
                with col:
                    if i < total_steps:
                        status = "active" if i == current_step else "completed" if i < current_step else ""
                        st.markdown(f"""
                            <div style='text-align: center;'>
                                <div style='width: 30px; height: 30px; background: {"linear-gradient(135deg, #667eea 0%, #764ba2 100%)" if i == current_step else "#10b981" if i < current_step else "#e2e8f0"}; 
                                     border-radius: 50%; margin: 0 auto 5px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;'>
                                    {i+1}
                                </div>
                                <div style='font-size: 0.8rem; color: {"#667eea" if i == current_step else "#666"};'>{step_names[i]}</div>
                            </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Show current group
            if current_step < len(all_groups):
                group = all_groups[current_step]
                
                # Group card
                st.markdown(f"""
                    <div class="group-card">
                        <div class="group-header">
                            <div class="group-icon">{group['icon']}</div>
                            <div>
                                <div class="group-title">{group['group_name']}</div>
                                <div class="group-description">{group.get('description', '')}</div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Render fields in 2 columns
                fields = group['fields']
                cols = st.columns(2)
                
                for idx, field in enumerate(fields):
                    with cols[idx % 2]:
                        value = render_field(field, f"step_{current_step}")
                        st.session_state.form_data[f"{current_step}_{field['key']}"] = value
                
                # Navigation buttons
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if current_step > 0:
                        if st.button("◀ Previous", use_container_width=True):
                            st.session_state.current_step -= 1
                            st.rerun()
                
                with col3:
                    if current_step < total_steps - 1:
                        if st.button("Next ▶", use_container_width=True, type="primary"):
                            st.session_state.current_step += 1
                            st.rerun()
                    else:
                        if st.button("🚀 Generate", use_container_width=True, type="primary"):
                            if not all([company_name, industry, region]):
                                st.error("Please complete company profile")
                            else:
                                st.balloons()
                                st.success("Document generated successfully!")
                                new_id = len(MOCK_DRAFTS) + len(st.session_state.generated_docs) + 1
                                new_draft = {
                                    "id": new_id,
                                    "name": selected_doc,
                                    "status": "draft",
                                    "version": st.session_state.form_data.get("0_version", "1.0"),
                                    "created": datetime.now().strftime("%Y-%m-%d"),
                                    "department": department
                                }
                                st.session_state.generated_docs.append(new_draft)
                                st.session_state.selected_draft_id = new_id
                                st.rerun()
    else:
        st.info("👈 Select a document template from sidebar")

with tab2:
    st.markdown("### 📚 Document Library")
    
    # Search
    search = st.text_input("🔍 Search", placeholder="Type to search...", key="lib_search")
    
    # Display drafts
    all_drafts = MOCK_DRAFTS + st.session_state.generated_docs
    filtered = [d for d in all_drafts if search.lower() in d['name'].lower()] if search else all_drafts
    
    if filtered:
        for i in range(0, len(filtered), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(filtered):
                    draft = filtered[i + j]
                    with cols[j]:
                        st.markdown(f"""
                            <div class="draft-card">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <div>
                                        <strong>{draft['name'][:25]}{'...' if len(draft['name']) > 25 else ''}</strong>
                                        <div style="font-size: 0.8rem; color: #666;">v{draft['version']}</div>
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
                                st.session_state.generated_docs = [d for d in st.session_state.generated_docs if d["id"] != draft["id"]]
                                st.rerun()
    else:
        st.info("No documents found")

# ---------------- DOCUMENT PREVIEW ----------------
if st.session_state.selected_draft_id:
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    all_drafts = MOCK_DRAFTS + st.session_state.generated_docs
    draft = next((d for d in all_drafts if d["id"] == st.session_state.selected_draft_id), None)
    
    if draft:
        # Toolbar
        cols = st.columns([3, 1, 1, 1])
        with cols[0]:
            st.markdown(f"**{draft['name']}**  v{draft['version']}")
        with cols[1]:
            if st.button("📥 PDF", use_container_width=True):
                st.success("Download started")
        with cols[2]:
            if st.button("📥 DOCX", use_container_width=True):
                st.success("Download started")
        with cols[3]:
            if st.button("✖️", use_container_width=True):
                st.session_state.selected_draft_id = None
                st.rerun()
        
        # Document preview
        st.markdown('<div class="document-paper">', unsafe_allow_html=True)
        st.markdown(f"<h1>{draft['name']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>Company: {company_name}</p>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Sample content
        sections = [
            "This document serves as the official policy for all employees.",
            "All employees must adhere to the guidelines outlined herein.",
            "Questions regarding this document should be directed to HR."
        ]
        for i, content in enumerate(sections):
            st.markdown(f"<h2>Section {i+1}</h2>", unsafe_allow_html=True)
            st.markdown(content)
        
        st.markdown('</div>', unsafe_allow_html=True)
