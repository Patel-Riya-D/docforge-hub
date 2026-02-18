import json
import os
from backend.registry.validator import validate_document_schema   
from backend.registry.resolver import resolve_document 


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../")
)

DOCUMENT_REGISTRY_PATH = os.path.join(BASE_DIR, "document_registry")


def load_document_json(department: str, document_filename: str) -> dict:
    department = department.lower()

    file_path = os.path.join(
        DOCUMENT_REGISTRY_PATH,
        department,
        document_filename
    )

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Document file not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        document_data = json.load(f)

    validate_document_schema(document_data)

    return document_data
