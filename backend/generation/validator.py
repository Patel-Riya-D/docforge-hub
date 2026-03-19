"""
validator.py

This module validates generated document drafts in the DocForge Hub system.

It ensures that AI-generated content meets enterprise standards by combining:
- LLM-based semantic validation (compliance, tone, completeness)
- Rule-based hard validation checks (repetition, formatting issues)

Key Features:
- Full-document validation using LLM
- Detection of compliance and structural issues
- Fallback handling for invalid LLM responses
- Additional hard-coded quality checks

Validation Output:
{
    "status": "PASS" | "FAIL",
    "issues": [list of problems],
    "risk_score": float,
    "confidence_score": float
}

This module acts as the final quality gate before document approval.
"""
import os
from openai import AzureOpenAI
from backend.prompts.loader import load_prompt
import json
from dotenv import load_dotenv
load_dotenv()
from langchain_core.prompts import ChatPromptTemplate
from backend.generation.llm_provider import get_llm
import json

llm = get_llm()


def validate_draft_llm(draft: dict):
    """
    Validate a generated draft using LLM-based evaluation.

    This function analyzes the full document content by:
    - Extracting paragraph text from all sections
    - Constructing a structured validation prompt
    - Calling LLM to evaluate compliance, quality, and completeness

    Args:
        draft (dict): Generated document draft containing:
            - source_document metadata
            - sections with blocks (paragraphs, tables, etc.)

    Returns:
        dict: Validation result containing:
            - status (str): "PASS" or "FAIL"
            - issues (list): Identified problems
            - risk_score (float): Risk/compliance score
            - confidence_score (float): Model confidence

    Behavior:
        - Uses predefined validation prompt template
        - Enforces strict JSON-only response from LLM
        - Handles parsing errors with fallback response

    Fallback:
        If LLM output is invalid JSON:
        returns:
        {
            "status": "FAIL",
            "issues": ["Validation model returned invalid JSON"],
            "risk_score": 0,
            "confidence_score": 0
        }
    """

    sections_text = ""

    for section in draft["sections"]:

        combined_content = " ".join(
            block["content"]
            for block in section["blocks"]
            if block["type"] == "paragraph"
        )

        sections_text += f"""
    Section: {section['name']}
    Content:
    {combined_content}
    ---------------------------------
    """

    prompt_template = load_prompt("validation_prompt")

    formatted_prompt = prompt_template.format(
        document_type=draft["source_document"]["internal_type"],
        risk_level=draft["source_document"]["risk_level"],
        department=draft["source_document"]["department"],
        sections_content=sections_text
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a strict enterprise compliance validator. Return ONLY valid JSON."),
        ("human", formatted_prompt)
    ])

    chain = prompt | llm
    result = chain.invoke({})

    raw_output = result.content

    try:
        parsed = json.loads(raw_output)
        return parsed
    except:
        return {
            "status": "FAIL",
            "issues": ["Validation model returned invalid JSON"],
            "risk_score": 0,
            "confidence_score": 0
        }

def hard_validation_checks(draft):
    """
    Perform rule-based validation checks on generated drafts.

    This function complements LLM validation by detecting:
    - Repetition of enforcement language
    - Excessive company name repetition
    - Overuse of compliance frameworks (e.g., SOC 2, GDPR)

    Args:
        draft (dict): Generated document draft.

    Returns:
        list[str]: List of detected issues.

    Checks Performed:
        1. Enforcement phrase repetition
        2. Company name overuse in sections
        3. Compliance framework overuse

    Notes:
        - Ensures content readability and avoids redundancy
        - Acts as a deterministic safety layer alongside LLM validation
    """
    issues = []

    # Enforcement phrase repetition
    enforcement_phrase = "Violations of this policy may result in disciplinary action"
    full_text = " ".join(
    " ".join(
        block["content"]
        for block in s["blocks"]
        if block["type"] == "paragraph"
    )
    for s in draft["sections"]
    )

    if full_text.count(enforcement_phrase) > 1:
        issues.append("Enforcement language repeated more than once.")
    
    ############remove repetation
    company_name = draft["source_document"]["document_name"]

    for section in draft["sections"]:
        combined_content = " ".join(
            block["content"]
            for block in section["blocks"]
            if block["type"] == "paragraph"
        )

        if combined_content.count(company_name) > 2:
            issues.append(f"Company name repeated excessively in section {section['name']}.")


    frameworks = ["SOC 2", "GDPR", "ISO 27001"]

    for fw in frameworks:
        if full_text.count(fw) > 2:
            issues.append(f"Compliance framework '{fw}' repeated excessively.")

    return issues