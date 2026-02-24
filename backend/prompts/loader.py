from pathlib import Path

PROMPT_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """
    Load a prompt template from backend/prompts/*.txt
    """
    path = PROMPT_DIR / f"{name}.txt"

    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    return path.read_text(encoding="utf-8")


def build_section_prompt(context: dict) -> str:
    """
    Company:
    - Name: {company_profile["company_name"]}
    - Industry: {company_profile["industry"]}
    - Employees: {company_profile["employee_count"]}
    - Region: {", ".join(company_profile["regions"])}
    - Compliance: {", ".join(company_profile["compliance_frameworks"])}
    - Jurisdiction: {company_profile["default_jurisdiction"]}

    """
    template = load_prompt("section")

    from collections import defaultdict
    return template.format_map(defaultdict(str, context))
