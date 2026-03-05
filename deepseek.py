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




###################################################app.py
import os
import streamlit as st
import requests
from backend.utils.schema_merger import merge_input_groups
import pandas as pd
from backend.generation.question_label_enhancer import enhance_label

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

if "pending_questions" not in st.session_state:
    st.session_state.pending_questions = []

if "question_answers" not in st.session_state:
    st.session_state.question_answers = {}

if "questions_generated" not in st.session_state:
    st.session_state.questions_generated = False

if "questions_initialized" not in st.session_state:
    st.session_state.questions_initialized = False

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
                raw_label = field["label"]

                cache_key = f"enhanced_{document_name}_{raw_label}"

                if cache_key not in st.session_state:
                    st.session_state[cache_key] = enhance_label(raw_label, document_name)

                label = st.session_state[cache_key]

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
                raw_label = field["label"]

                cache_key = f"enhanced_{document_name}_{raw_label}"

                if cache_key not in st.session_state:
                    st.session_state[cache_key] = enhance_label(raw_label, document_name)

                label = st.session_state[cache_key]

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

    # Reset questions if user switches document
    if st.session_state.get("current_doc") != document_filename:
        st.session_state.current_doc = document_filename
        st.session_state.pending_questions = []
        st.session_state.question_answers = {}
        st.session_state.questions_generated = False
        st.session_state.questions_initialized = False

        for k in list(st.session_state.keys()):
            if k.startswith("aiq_"):
                del st.session_state[k]


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

    # if not st.session_state.questions_initialized:

    #     safe_inputs = {}

    #     for key, value in user_inputs.items():
    #         if hasattr(value, "isoformat"):
    #             safe_inputs[key] = value.isoformat()
    #         else:
    #             safe_inputs[key] = value

    #     questions_response = requests.post(
    #         f"{API_BASE_URL}/documents/generate-questions",
    #         json={
    #             "department": department.lower(),
    #             "document_filename": document_filename,
    #             "company_profile": {
    #                 "company_name": company_name,
    #                 "industry": industry,
    #                 "employee_count": employee_count,
    #                 "regions": [region],
    #                 "compliance_frameworks": [compliance],
    #                 "default_jurisdiction": jurisdiction
    #             },
    #             "document_inputs": safe_inputs
    #         }
    #     )
    #     # st.write("AI Question API Response:", questions_response.json())
        
    #     if questions_response.status_code == 200:
    #         st.session_state.pending_questions = questions_response.json().get("questions", [])
        
    #     st.session_state.questions_initialized = True

    # ---------------- AI CLARIFICATION QUESTIONS ----------------

    if st.session_state.pending_questions:

        st.divider()
        st.subheader("Additional Governance Information")

        for q in st.session_state.pending_questions:
            key = q["key"]
            question_text = q["question"]
            q_type = q.get("type", "text")

            unique_key = f"aiq_{department}_{document_filename}_{key}"

            if q_type == "textarea":
                answer = st.text_area(question_text, key=unique_key)
            else:
                answer = st.text_input(question_text, key=unique_key)

            st.session_state.question_answers[key] = answer

    # ---------------- GENERATE BUTTON ----------------

    if st.button("Generate Draft", use_container_width=True):

        if not company_name or not industry or not region or not jurisdiction:
            st.error("Please complete company profile before generating.")
            st.stop()

        if validation_errors:
            for err in validation_errors:
                st.error(err)
            st.stop()

        # Convert date inputs
        for key, value in user_inputs.items():
            if hasattr(value, "isoformat"):
                user_inputs[key] = value.isoformat()

        # Merge AI clarification answers
        user_inputs.update(st.session_state.question_answers)

        # If questions are pending but unanswered, block generation
        if st.session_state.pending_questions:
            for key, answer in st.session_state.question_answers.items():
                if not answer:
                    st.error("Please answer all additional questions before generating the draft.")
                    st.stop()

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

        result = response.json()

        if result.get("status") == "questions_required":
            new_questions = result.get("questions", [])

            # ✅ Only update if these are genuinely NEW questions (not the same ones)
            existing_keys = {q["key"] for q in st.session_state.pending_questions}
            new_keys = {q["key"] for q in new_questions}

            if new_keys != existing_keys:
                st.session_state.pending_questions = new_questions
                # Clear only old answers for new keys
                for q in new_questions:
                    if q["key"] not in st.session_state.question_answers:
                        st.session_state.question_answers[q["key"]] = ""
                st.warning("Additional information required before generating the draft.")
                st.rerun()
            else:
                # Same questions returned again — answers weren't accepted, warn user
                st.error("Please ensure all additional questions are answered correctly.")

        elif result.get("status") == "draft_saved":
            st.success("Draft Generated Successfully")
            st.session_state.selected_draft_id = result["draft_id"]
            st.session_state.pending_questions = []
            st.session_state.question_answers = {}
            st.rerun()

        else:
            st.error("Draft generation failed")

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
            # blocks = section["content"]
            blocks = section.get("blocks", [])

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
                    
                    elif block.get("type") == "diagram":
                        # st.write("DIAGRAM BLOCK FOUND:", block)  # ← debug line
                        diagram_url = block.get("diagram_url")
                        image_path = block.get("render_path")
                        if diagram_url:
                            col_l, col_m, col_r = st.columns([1, 3, 1])
                            with col_m:
                                st.image(f"{API_BASE_URL}{diagram_url}")
                        elif image_path and os.path.exists(image_path):
                            with open(image_path, "rb") as f:
                                st.image(f.read(), use_container_width=True)
                        else:
                            st.warning(f"Diagram not available — url: {diagram_url}, path: {image_path}")
            
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

                blocks = section.get("blocks") or []

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
                    
                    elif block.get("type") == "diagram":
                        # st.write("DIAGRAM BLOCK FOUND:", block)  # ← debug line
                        diagram_url = block.get("diagram_url")
                        image_path = block.get("render_path")
                        if diagram_url:
                            st.image(f"{API_BASE_URL}{diagram_url}", use_container_width=True)
                        elif image_path and os.path.exists(image_path):
                            with open(image_path, "rb") as f:
                                st.image(f.read(), use_container_width=True)
                        else:
                            st.warning(f"Diagram not available — url: {diagram_url}, path: {image_path}")

        else:
            st.divider()
            st.info("Full document preview will be available after all sections are approved.")


    else:
        st.error("Failed to load draft")
