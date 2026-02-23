import uuid
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from backend.models.company_profile import CompanyProfile
from backend.prompts.loader import build_section_prompt, load_prompt
from backend.generation.validator import validate_draft_llm
from backend.prompts.type_behavior import get_type_behavior, should_generate_toc, get_forbidden_phrases
from backend.prompts.risk_behavior import get_risk_behavior
from backend.prompts.section_rules import get_section_rules, get_section_word_limit
from langchain_core.prompts import ChatPromptTemplate
from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re

llm = get_llm()

load_dotenv()

def _is_table_section(section_name: str) -> bool:
    table_sections = [
        "roles and responsibilities",
        "compliance matrix",
        "approval matrix",
        "escalation path"
    ]
    return section_name.lower() in table_sections

def _should_generate_section(doc_type: str, section_name: str) -> bool:
    """
    Returns False for sections that must be skipped for this doc type.
    Currently gates:
      - Table of Contents / Index  →  only for POLICY, SOP, REPORT, HANDBOOK, STRATEGY, PROPOSAL
    All other sections always return True.
    """
    section_lower = section_name.lower()

    toc_keywords = ["table of contents", "index", "contents page"]
    is_toc_section = any(kw in section_lower for kw in toc_keywords)

    if is_toc_section:
        return should_generate_toc(doc_type)

    return True



# SECTION VALIDATOR
# Checks the LLM output for common quality issues.

def _validate_section_output(
    content: str,
    section_name: str,
    doc_type: str
) -> dict:
    """
    Validates a single generated section.

    Returns:
        {
            "valid": bool,
            "issues": list[str],
            "word_count": int,
            "min_words": int,
            "max_words": int
        }
    """
    issues = []
    word_count = len(content.split())
    min_words, max_words = get_section_word_limit(doc_type, section_name)

    repetitive_phrases = [
        "this section constitutes a binding policy requirement",
        "all employees are subject to this policy from their start date",
        "violations of this policy may result in disciplinary action",
        "this policy is reviewed annually"
    ]

    for phrase in repetitive_phrases:
        if phrase in content.lower():
            issues.append(f"Repetitive boilerplate detected: '{phrase}'")
    
    instruction_phrases = [
    "enter the",
    "provide the",
    "complete all fields",
    "insert the",
    "fill in",
    "specify the",
    "record the following"
    ]

    for phrase in instruction_phrases:
        if phrase in content.lower() and doc_type not in ["FORM", "TEMPLATE"]:
            issues.append(f"Instructional language not allowed in {doc_type}: '{phrase}'")


    #  Word count checks 
    if word_count < min_words:
        issues.append(
            f"Too short: {word_count} words (minimum required: {min_words})"
        )

    if word_count > max_words:
        issues.append(
            f"Too long: {word_count} words (maximum allowed: {max_words})"
        )

    #  Section heading repeated inside content body 
    if section_name.lower() in content[:200].lower():
        issues.append(
            "Section heading is repeated inside the content body. "
            "Heading is added externally — remove it from the content."
        )

    #  Placeholder / unfilled text 
    bad_placeholders = [
        "[TO BE FILLED]", "[INSERT HERE]", "[TBD]",
        "TODO:", "[PLACEHOLDER]", "[ADD CONTENT HERE]",
        "[COMPANY NAME]", "[DATE]"
    ]
    for ph in bad_placeholders:
        if ph.upper() in content.upper():
            issues.append(f"Unfilled placeholder found: '{ph}'")

    #  Model preamble leak 
    preamble_phrases = [
        "here is the content",
        "here is the section",
        "below is the content",
        "i'll now generate",
        "the following section",
        "as requested, here"
    ]
    content_start = content[:120].lower()
    for phrase in preamble_phrases:
        if phrase in content_start:
            issues.append(
                f"Model added preamble text: '{phrase}'. "
                "Output must start directly with document content."
            )

    #  Forbidden phrases 
    forbidden = get_forbidden_phrases(doc_type)
    for phrase in forbidden:
        if phrase.lower() in content.lower():
            issues.append(f"Forbidden phrase detected: '{phrase}'")

    #  Empty output 
    if not content.strip():
        issues.append("Generated content is empty.")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "word_count": word_count,
        "min_words": min_words,
        "max_words": max_words
    }


# SINGLE SECTION GENERATOR
# Calls AzureOpenAI for one section and validates output.

def _generate_single_section(
    section_name: str,
    mandatory: bool,
    registry_doc: dict,
    company_block: str,
    company_profile: dict,
    inputs_block: str,
    industry_context: str,
    user_notes: str,
    all_sections: list,
    retry: bool = False,
    previous_issues: list = None
) -> dict:
    """
    Generates content for one section.
    Validates the output and returns the full section result.

    Returns:
        {
            "name": str,
            "mandatory": bool,
            "content": str,
            "section_validation": dict   ← NEW: per-section quality result
        }
    """
    doc_type      = registry_doc["internal_type"]
    risk_level    = registry_doc["risk_level"]
    type_behavior_data  = get_type_behavior(doc_type)
    tone = type_behavior_data.get("tone", "professional")
    voice = type_behavior_data.get("voice", "third-person")
    format_style = type_behavior_data.get("format", "")
    rules = type_behavior_data.get("rules", "")
    avg_section_words = type_behavior_data.get("avg_section_words", "")
    risk_behavior  = get_risk_behavior(risk_level)
    section_rules  = get_section_rules(doc_type, section_name)
    
    # Convert CompanyProfile to dict if needed
    if company_profile is not None and not isinstance(company_profile, dict):
        company_profile = company_profile.dict() if hasattr(company_profile, 'dict') else dict(company_profile)
    
    company_name = company_profile.get("company_name", "") if company_profile else ""
    industry = company_profile.get("industry", "") if company_profile else ""
    employee_count = company_profile.get("employee_count", "") if company_profile else ""
    region = ", ".join(company_profile.get("regions", [])) if company_profile else ""
    jurisdiction = company_profile.get("default_jurisdiction", "") if company_profile else ""

    # Build TOC section list string for the prompt
    all_sections_str = "\n".join(
        f"{i+1}. {s['name']}"
        for i, s in enumerate(all_sections)
    )
    min_words, max_words = get_section_word_limit(doc_type, section_name)
    if max_words > 300:
        max_words = 300

    forbidden_phrases = get_forbidden_phrases(doc_type)

    context = {
        "document_name":   registry_doc.get("document_name", ""),
        "document_type":   doc_type,
        "risk_level":      risk_level,
        "section_name":    section_name,
        "mandatory":       str(mandatory),
        "company_profile": company_profile if company_profile else {},
        "document_inputs": inputs_block,
        "industry_context": industry_context,
        "type_behavior":   rules if rules else "",
        "tone": tone if tone else "professional",
        "voice": voice if voice else "third-person",
        "format_style": format_style if format_style else "",
        "avg_section_words": avg_section_words if avg_section_words else "",
        "risk_behavior":   risk_behavior if risk_behavior else "",
        "section_rules":   section_rules if section_rules else "",
        "all_sections":    all_sections_str,
        "toc_required":    str(should_generate_toc(doc_type)).upper(),
        "min_words": min_words,
        "max_words": max_words,
        "company_name": str(company_name) if company_name else "",
        "industry": str(industry) if industry else "",
        "employee_count": str(employee_count) if employee_count else "",
        "region": str(region) if region else "",
        "jurisdiction": str(jurisdiction) if jurisdiction else "",
        "forbidden_phrases": "\n".join(forbidden_phrases) if forbidden_phrases else ""
    }

    try:
        base_prompt = build_section_prompt(context)
    except Exception as e:
        print(f"[ERROR] Failed to build prompt for section '{section_name}': {str(e)}")
        raise

    # ── Add retry context if this is a re-generation ───────
    retry_block = ""
    if retry and previous_issues:
        retry_block = (
            "\n\nPREVIOUS ATTEMPT FAILED VALIDATION — FIX ALL ISSUES BELOW:\n"
            + "\n".join(f"  • {issue}" for issue in previous_issues)
            + "\n\nRe-generate the section addressing every issue listed above.\n"
        )

    full_prompt = f"""
{base_prompt}
{retry_block}
Additional Notes:
{user_notes or "None provided."}
""".strip()

    system_message = f"""
    You are generating the FINAL VERSION of an enterprise {doc_type} document.

    You are NOT:
    - Writing instructions
    - Writing guidance
    - Writing meta commentary
    - Writing a template unless document_type == TEMPLATE
    - Writing placeholders unless document_type == FORM or TEMPLATE

    You ARE:
    - Writing the actual content as it will appear in the published document.

    STRICT LENGTH RULE:
    - Between {min_words} and {max_words} words.
    - Do NOT exceed limit.
    - If exceeded, you FAIL.

    STRICT OUTPUT RULES:
    - Start directly with content.
    - Do NOT repeat section title.
    - Do NOT explain what to do.
    - Do NOT include examples unless explicitly required.
    - Do NOT add filler language.

    SECTION CONTEXT CONTROL:
    - Write content ONLY relevant to the section name.
    - Do NOT introduce topics that belong to other enterprise policies.
    - Do NOT expand scope beyond the purpose of this specific document.

    """

    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=full_prompt)
    ]

    try:
        response = llm.invoke(messages)
    except Exception as e:
        print(f"[ERROR] LLM invocation failed for section '{section_name}': {str(e)}")
        raise
    
    try:
        content = getattr(response, "content", str(response)).strip()
    except:
        content = str(response).strip()

    structured_content = None
    cleaned = content.strip()

    # Remove code fences
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()

    # 🚨 HARD GUARD: reject simple string outputs like "table"
    parsed = None
    if cleaned and cleaned.startswith('{'):
        try:
            parsed = json.loads(cleaned)
        except Exception:
            # If JSON parsing fails, treat entire output as text
            parsed = None
            # Don't use the cleaned content if it looks like broken JSON
            if cleaned.startswith('"') or cleaned.startswith('['):
                content = ""

    # 🚨 If JSON is not dict → ignore it
    if not isinstance(parsed, dict):
        parsed = None

    # ───── TABLE HANDLING ─────
    if parsed and "table" in parsed:

        # 🚨 Only allow table for approved sections
        if not _is_table_section(section_name):
            print(f"[BLOCKED] Table returned for non-table section: {section_name}")
            structured_content = None

        else:
            table_obj = parsed.get("table")

            if (
                isinstance(table_obj, dict)
                and isinstance(table_obj.get("headers"), list)
                and isinstance(table_obj.get("rows"), list)
            ):
                structured_content = {
                    "table": {
                        "headers": table_obj["headers"],
                        "rows": table_obj["rows"]
                    }
                }
                content = ""
            else:
                print(f"[INVALID TABLE STRUCTURE] {section_name}")
                structured_content = None

    # Direct headers/rows support
    elif parsed and "headers" in parsed and "rows" in parsed:
        if _is_table_section(section_name):
            structured_content = {
                "table": {
                    "headers": parsed["headers"],
                    "rows": parsed["rows"]
                }
            }
            content = ""
        else:
            structured_content = None

    # except Exception as e:
    #     print(f"[JSON ERROR] {section_name}: {e}")
    #     structured_content = None

    # If we still have no structured content but content looks like broken JSON, clear it
    if not structured_content and content and content.strip().startswith('"') and content.strip().endswith('"'):
        # This looks like a failed JSON string, not valid text content
        content = ""

    if content and not structured_content:  # Only trim text content
        max_words_allowed = max_words
        words = content.split()
        if len(words) > max_words_allowed:
            content = " ".join(words[:max_words_allowed])

    # Validate output
    if structured_content:
        # Tables are automatically valid
        section_validation = {
            "valid": True,
            "issues": [],
            "word_count": 0,
            "min_words": 0, 
            "max_words": 0
        }
    elif content.strip():
        section_validation = _validate_section_output(
            content=content,
            section_name=section_name,
            doc_type=doc_type
        )
    else:
        # Empty content - mark as invalid
        section_validation = {
            "valid": False,
            "issues": ["No valid content generated"],
            "word_count": 0,
            "min_words": min_words,
            "max_words": max_words
        }
    print(f"[RAW LLM OUTPUT] {section_name}: {cleaned}")
    print(f"[DEBUG] {section_name} - Type: {'TABLE' if structured_content else 'TEXT'}")
    if structured_content:
        print(f"[DEBUG] Table headers: {structured_content['table']['headers']}")
        print(f"[DEBUG] Table rows: {len(structured_content['table']['rows'])}")

    return {
        "name":               section_name,
        "mandatory":          mandatory,
        "content":            content,
        "structured_content": structured_content,
        "section_validation": section_validation
    }


# SECTION REGENERATION (User-triggered from UI)

def regenerate_section_llm(draft: dict, section: dict, issues: list) -> str:

    template = load_prompt("regeneration_prompt")

    formatted_prompt = template.format(
        document_type=draft["source_document"]["internal_type"],
        risk_level=draft["source_document"]["risk_level"],
        department=draft["source_document"]["department"],
        section_name=section["name"],
        original_content=section["content"],
        issues="\n".join(issues)
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert enterprise document improver."),
        ("human", formatted_prompt)
    ])

    chain = prompt | llm
    result = chain.invoke({})

    return result.content.strip()

def _compress_sections(sections, max_words):
    per_section_budget = max_words // len(sections)

    for s in sections:
        words = s["content"].split()
        if len(words) > per_section_budget:
            s["content"] = " ".join(words[:per_section_budget])

    return sections

# MAIN GENERATE DRAFT

def generate_draft(
    registry_doc: dict,
    department: str,
    document_filename: str,
    company_profile: CompanyProfile = None,
    document_inputs: dict = None,
    user_notes: str = None
) -> dict:
    """
    Generates a full document draft section by section.

    Flow:
      1. Build draft skeleton
      2. Format company profile + user inputs
      3. For each section:
            a. TOC gate  → skip if not needed for this doc type
            b. Generate  → call LLM
            c. Validate  → check word count, placeholders, preamble, etc.
            d. Auto-retry once if validation fails
      4. Run full-draft AI validation with regeneration loop
      5. Return final draft

    Returns: draft dict (same shape as before + section_validation per section)
    """

    #  Step 1: Draft  
    draft = {
        "draft_id": str(uuid.uuid4()),
        "source_document": {
            "department":           department,
            "document_filename":    document_filename,
            "document_name":        registry_doc["document_name"],
            "internal_type":        registry_doc["internal_type"],
            "risk_level":           registry_doc["risk_level"],
            "compliance_alignment": registry_doc.get("compliance_alignment", [])
        },
        "version": "v1.0",
        "status": "DRAFT",
        "generation_metadata": {
            "generated_at":    datetime.now(timezone.utc).isoformat(),
            "generated_by":    "azure_openai",
            "deterministic":   True,
            "prompt_version":  "v2",           # ← bumped to v2 after enhancement
            "toc_generated":   should_generate_toc(registry_doc["internal_type"]),
            "retry_count":     0
        },
        "sections": [],
        "validation": {
            "status": "NOT_RUN",
            "issues": []
        },
        "approval": {
            "required":     registry_doc["approval_required"],
            "approved":     False,
            "approved_by":  None,
            "approved_at":  None
        }
    }

    #  Step 2: Format context blocks 
    company_block = ""
    if company_profile:
        company_block = (
            f"Company Name: {company_profile.get('company_name')}\n"
            f"Industry: {company_profile.get('industry')}\n"
            f"Employee Count: {company_profile.get('employee_count')}\n"
            f"Region: {', '.join(company_profile.get('regions', []))}\n"
            f"Compliance: {', '.join(company_profile.get('compliance_frameworks', []))}\n"
            f"Jurisdiction: {company_profile.get('default_jurisdiction')}\n"
        )

    inputs_block = ""
    if document_inputs:
        for key, value in document_inputs.items():
            inputs_block += f"{key}: {value}\n"

    # Validate that registry_doc has required fields
    if "sections" not in registry_doc or not registry_doc["sections"]:
        print(f"[ERROR] No sections found in registry_doc")
        print(f"[ERROR] Registry doc keys: {registry_doc.keys()}")
        raise ValueError("Document has no sections defined")

    all_sections     = registry_doc["sections"]

    #  Step 3: Generate each section 
    SECTION_MAX_RETRIES = 1   # One auto-retry per section

    industry_context = load_prompt("industry_context")

    for section in all_sections:
        section_name = section.get("name")
        mandatory    = section.get("mandatory", True)
        
        # Skip sections without names
        if not section_name:
            print(f"[WARN] Skipping section without name: {section}")
            continue

        if section_name.lower() in [
            "security",
            "compliance",
            "data protection",
            "incident response"
        ]: 
            industry_block = industry_context
        else:
            industry_block = ""  


        if not _should_generate_section(
            registry_doc["internal_type"], section_name
        ):
            print(f"[SKIP] '{section_name}' — not required for {registry_doc['internal_type']}")
            continue

        print(f"[GEN]  Generating section: '{section_name}'")

        #  First attempt 
        section_result = _generate_single_section(
            section_name=section_name,
            mandatory=mandatory,
            registry_doc=registry_doc,
            company_profile=company_profile,
            company_block=company_block,
            inputs_block=inputs_block,
            industry_context=industry_block,
            user_notes=user_notes,
            all_sections=all_sections,
            retry  =False
        )

        #  Section-level auto-retry 
        if not section_result["section_validation"]["valid"]:
            issues = section_result["section_validation"]["issues"]
            print(
                f"[WARN] Section '{section_name}' failed validation "
                f"({len(issues)} issue(s)). Retrying..."
            )

            retry_result = _generate_single_section(
                section_name=section_name,
                mandatory=mandatory,
                registry_doc=registry_doc,
                company_block=company_block,
                company_profile=company_profile,    
                inputs_block=inputs_block,
                industry_context=industry_block,
                user_notes=user_notes,
                all_sections=all_sections,
                retry=True,
                previous_issues=issues
            )

            # Use retry result only if it's better (or equal)
            if (
                retry_result["section_validation"]["valid"]
                or len(retry_result["section_validation"]["issues"])
                <= len(issues)
            ):
                section_result = retry_result

        draft["sections"].append(section_result)
        print(
            f"[DONE] '{section_name}' — "
            f"{section_result['section_validation']['word_count']} words | "
            f"valid: {section_result['section_validation']['valid']}"
        )

        #  Global document word cap (max ~2000 words ≈ 4 pages) 

        MAX_TOTAL_WORDS = 1800
        total_words = sum(
            s["section_validation"]["word_count"]
            for s in draft["sections"]
        )

        print(f"[INFO] Total document words before trim: {total_words}")

        if total_words > MAX_TOTAL_WORDS:
            draft["sections"] = _compress_sections(draft["sections"], MAX_TOTAL_WORDS)


    #  Step 4: Full-draft AI validation + regeneration loop 
    MAX_DRAFT_RETRIES = 2
    retry_count       = 0

    validation_result = {"status": "NOT_RUN", "issues": []}

    while retry_count <= MAX_DRAFT_RETRIES:

        try:
            validation_result = validate_draft_llm(draft)
        except Exception as e:
            validation_result = {
                "status": "ERROR",
                "issues": [f"Validation failed: {str(e)}"]
            }

        print(f"[VALIDATE] Status: {validation_result['status']} | Retry: {retry_count}")

        draft["validation"]                            = validation_result
        draft["generation_metadata"]["retry_count"]    = retry_count

        if validation_result["status"] == "PASS":
            draft["status"] = "READY_FOR_APPROVAL"
            break
        else:
            draft["status"] = "NEEDS_REVIEW"

        if retry_count < MAX_DRAFT_RETRIES:
            issues = validation_result.get("issues", [])

            for section in draft["sections"]:
                if section["mandatory"]:
                    try:
                        improved = regenerate_section_llm(
                            draft=draft,
                            section=section,
                            issues=issues
                        )
                        section["content"] = improved

                        # Re-run JSON parsing logic
                        section_result = _generate_single_section(
                            section_name=section["name"],
                            mandatory=True,
                            registry_doc=registry_doc,
                            company_profile=company_profile,
                            company_block="",
                            inputs_block="",
                            industry_context="",
                            user_notes="",
                            all_sections=[],
                            retry=False
                        )

                        # Only update text from regeneration
                        section["content"] = improved
                        section["structured_content"] = None
                        section["section_validation"] = {
                            "valid": True,
                            "issues": [],
                            "word_count": len(improved.split()),
                            "min_words": 0,
                            "max_words": 0
                        }

                    except Exception:
                        continue

            retry_count += 1
        else:
            draft["status"] = "NEEDS_REVIEW"
            break

    print("DOC TYPE:", registry_doc["internal_type"])

    print(f"[FINAL] Draft status: {draft['status']} | "
          f"Sections: {len(draft['sections'])}")

    return draft