import os
from openai import AzureOpenAI
from backend.prompts.loader import load_prompt
import json
from dotenv import load_dotenv
load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_LLM_KEY"),
    api_version=os.getenv("AZURE_LLM_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_LLM_ENDPOINT"),
)


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

    full_prompt = prompt_template.format(
        document_type=draft["source_document"]["internal_type"],
        risk_level=draft["source_document"]["risk_level"],
        department=draft["source_document"]["department"],
        sections_content=sections_text
    )

    response = client.chat.completions.create(
        model=os.getenv("AZURE_LLM_DEPLOYMENT_41_MINI"),
        messages=[
            {"role": "system", "content": "You are a strict enterprise compliance validator."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.2,
    )

    raw_output = response.choices[0].message.content

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
