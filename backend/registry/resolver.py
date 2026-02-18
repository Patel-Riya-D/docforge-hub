import json
import os


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../")
)

DOCUMENT_TYPES_PATH = os.path.join(BASE_DIR, "document_types")


def load_document_type(internal_type: str) -> dict:
    """
    Load document_type rules (policy.json, sop.json, etc.)
    """
    filename = f"{internal_type.lower()}.json"
    file_path = os.path.join(DOCUMENT_TYPES_PATH, filename)

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Document type definition not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def enforce_mandatory_sections(document: dict, type_rules: dict) -> None:
    """
    Ensure all mandatory sections from document_type exist in document.
    """
    required = set(type_rules.get("mandatory_sections", []))
    present = {s["name"] for s in document["sections"]}

    missing = required - present

    if missing:
        raise ValueError(
            f"Missing mandatory sections for {document['internal_type']}: {missing}"
        )


def resolve_document(document: dict) -> dict:
    """
    Merge document JSON with its document_type rules.
    """
    internal_type = document["internal_type"]
    type_rules = load_document_type(internal_type)


    # enforce_mandatory_sections(document, type_rules)

    # Merge resolved document
    resolved = {
        "document_name": document["document_name"],
        "department": document["department"],
        "internal_type": internal_type,

        # document value wins, fallback to type default
        "risk_level": document.get(
            "risk_level",
            type_rules.get("default_risk_level")
        ),

        "approval_required": document.get(
            "approval_required",
            type_rules.get("approval_required")
        ),

        "versioning_strategy": type_rules.get("versioning_strategy"),

        "sections": document["sections"],
        "mandatory_sections": type_rules.get("mandatory_sections", []),
        "allowed_formats": document["allowed_formats"],
        "compliance_alignment": document.get("compliance_alignment", [])
    }

    return resolved
