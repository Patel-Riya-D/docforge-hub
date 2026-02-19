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

    sections_text = ""

    for section in draft["sections"]:
        sections_text += f"""
Section: {section['name']}
Content:
{section['content']}
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
    issues = []

    # Enforcement phrase repetition
    enforcement_phrase = "Violations of this policy may result in disciplinary action"
    full_text = " ".join([s["content"] for s in draft["sections"]])

    if full_text.count(enforcement_phrase) > 1:
        issues.append("Enforcement language repeated more than once.")
    
    ############remove repetation
    company_name = draft["source_document"]["document_name"]

    for section in draft["sections"]:
        if section["content"].count(company_name) > 2:
            issues.append(f"Company name repeated excessively in section {section['name']}.")


    frameworks = ["SOC 2", "GDPR", "ISO 27001"]

    for fw in frameworks:
        if full_text.count(fw) > 2:
            issues.append(f"Compliance framework '{fw}' repeated excessively.")

    # Company name repetition

    for section in draft["sections"]:
        if section["content"].count(company_name) > 2:
            issues.append(f"Company name repeated excessively in section {section['name']}.")

    return issues
