import json
import os


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../")
)

SCHEMA_PATH = os.path.join(BASE_DIR, "schemas", "document_schema.json")


def load_schema() -> dict:
    """Load the global document schema."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_document_schema(document: dict) -> None:
    """
    Validate a document JSON against document_schema.json.
    Raises ValueError if validation fails.
    """

    schema = load_schema()

    for field in schema["required_fields"]:
        if field not in document:
            raise ValueError(f"Missing required field: '{field}'")

    for field, expected_type in schema["field_types"].items():
        if field in document:
            if expected_type == "string" and not isinstance(document[field], str):
                raise ValueError(f"Field '{field}' must be a string")

            if expected_type == "boolean" and not isinstance(document[field], bool):
                raise ValueError(f"Field '{field}' must be a boolean")

            if expected_type == "object" and not isinstance(document[field], dict):
                raise ValueError(f"Field '{field}' must be an object")

            if expected_type == "array" and not isinstance(document[field], list):
                raise ValueError(f"Field '{field}' must be an array")


    if document["internal_type"] not in schema["allowed_internal_types"]:
        raise ValueError(
            f"Invalid internal_type: {document['internal_type']}"
        )


    if document["risk_level"] not in schema["allowed_risk_levels"]:
        raise ValueError(
            f"Invalid risk_level: {document['risk_level']}"
        )

    for fmt in document["allowed_formats"]:
        if fmt not in schema["allowed_formats"]:
            raise ValueError(f"Invalid format: {fmt}")


    for idx, section in enumerate(document["sections"]):
        for field in schema["section_schema"]["required_fields"]:
            if field not in section:
                raise ValueError(
                    f"Section {idx} missing required field: '{field}'"
                )

        if not isinstance(section["name"], str):
            raise ValueError(f"Section {idx} 'name' must be string")

        if not isinstance(section["mandatory"], bool):
            raise ValueError(f"Section {idx} 'mandatory' must be boolean")
