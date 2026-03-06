import json
from difflib import SequenceMatcher
from langchain_core.messages import SystemMessage, HumanMessage
from backend.generation.llm_provider import get_llm

llm = get_llm()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def keyword_overlap_ratio(a: str, b: str) -> float:
    stop_words = {
        "what", "who", "which", "how", "is", "are", "the", "a", "an",
        "for", "of", "to", "and", "or", "in", "on", "at", "be", "will",
        "does", "do", "any", "this", "that", "it", "with", "under",
        "by", "as", "from", "their", "your", "our", "please", "provide",
        "specify", "describe", "detail", "details", "information", "about"
    }
    a_words = set(a.lower().split()) - stop_words
    b_words = set(b.lower().split()) - stop_words
    if not a_words or not b_words:
        return 0
    overlap = len(a_words & b_words)
    return overlap / min(len(a_words), len(b_words))


def is_duplicate(new_question: str, existing_questions: list) -> bool:
    for existing in existing_questions:
        if similarity(new_question, existing) > 0.75:
            return True
        if keyword_overlap_ratio(new_question, existing) > 0.75:
            return True
    return False


def generate_clarification_questions(registry_doc: dict,
                                     company_profile: dict,
                                     document_inputs: dict):

    company_fields = [
        "company_name", "industry", "employee_count",
        "regions", "compliance_frameworks", "default_jurisdiction"
    ]

    existing_fields = list(document_inputs.keys()) + company_fields

    # Collect ALL existing form question labels universally
    existing_questions = []
    for group in registry_doc.get("input_groups", []):
        for field in group.get("fields", []):
            label = field.get("label")
            if label:
                existing_questions.append(label)

    # Also collect from base_input_groups if present
    for group in registry_doc.get("base_input_groups", []):
        for field in group.get("fields", []):
            label = field.get("label")
            if label:
                existing_questions.append(label)

    existing_questions_text = "\n".join(f"- {q}" for q in existing_questions)

    try:
        sections = "\n".join(
            [f"- {s['name']}" for s in registry_doc.get("sections", [])]
        )

        prompt = f"""
You are an enterprise document intelligence engine.

Your task is to identify ONLY the critical missing information
that is NOT already collected in the form or company profile.

==============================
DOCUMENT METADATA
==============================
Document Name: {registry_doc.get("document_name")}
Internal Type: {registry_doc.get("internal_type")}
Risk Level: {registry_doc.get("risk_level")}

==============================
SECTIONS TO BE GENERATED
==============================
{sections}

==============================
DOCUMENT COMPLETENESS GOAL
==============================
Ensure each section has enough information to generate
a complete enterprise-grade document.

Examples:
- policies require enforcement mechanisms
- handbooks require benefits, conduct, grievance procedures
- employment letters require salary, start date, role details

==============================
COMPANY PROFILE (ALREADY PROVIDED)
==============================
{company_profile}

==============================
FORM QUESTIONS ALREADY COLLECTED
==============================
The following questions are ALREADY in the form.
DO NOT generate any question that covers the same topic,
even with different wording.

{existing_questions_text}

==============================
FIELDS ALREADY FILLED BY USER
==============================
These inputs already have values and MUST NOT be asked again.

{document_inputs}

==============================
INSTRUCTIONS
==============================
1. Only ask about information that is TRULY missing and critical.
2. NEVER repeat or rephrase any question from the form above.
3. NEVER ask about company profile fields.
4. NEVER ask about: company name, industry, employee count,
   regions, compliance frameworks, jurisdiction.
5. Ask between 5 and 12 questions depending on missing information.
6. Use short stable snake_case keys.
7. Before generating each question, check:
   - Is this topic already in the form questions? → SKIP
   - Is this already in user provided inputs? → SKIP
   - Is this in the company profile? → SKIP

==============================
QUESTION PRIORITY
==============================
Prioritize questions for sections that have little or no input.

Ask about:
- governance
- operational details
- compliance
- roles and responsibilities
- approvals

==============================
OUTPUT FORMAT (STRICT)
==============================
Return ONLY a valid JSON array. No markdown. No backticks. No explanation.

[
  {{
    "key": "snake_case_key",
    "question": "Your question here?",
    "type": "text"
  }}
]

Allowed types: text, textarea

If nothing is missing return: []
"""

        response = llm.invoke([
            SystemMessage(content=(
                "You are a document intelligence engine. "
                "Return ONLY a valid JSON array. "
                "No markdown, no backticks, no explanation. "
                "Never repeat questions already in the form."
            )),
            HumanMessage(content=prompt)
        ])

        content = response.content.strip()

        # Strip markdown fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        questions = json.loads(content)

        if not isinstance(questions, list):
            return []

        # ✅ Universal deduplication — works for ALL document types
        final_questions = []
        seen_keys = set()

        for q in questions:
            key = q.get("key")
            question_text = q.get("question", "")

            # Skip if no key
            if not key:
                continue

            # Skip duplicate keys
            if key in seen_keys:
                continue

            # Skip if already answered in document_inputs
            if key in document_inputs and document_inputs[key]:
                continue

            # Skip if question is duplicate of existing form questions
            if is_duplicate(question_text, existing_questions):
                continue

            # Skip if question is duplicate of already added questions
            if is_duplicate(question_text, [q["question"] for q in final_questions]):
                continue

            seen_keys.add(key)
            final_questions.append(q)

        MAX_AI_QUESTIONS = 12
        return final_questions[:MAX_AI_QUESTIONS]

    except Exception as e:
        print("QUESTION ENGINE ERROR:", str(e))
        return []