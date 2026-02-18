import json
import os

DOCUMENT_TYPES_PATH = "/home/riyap/DocForage/document_types"

def load_base_type(internal_type: str):
    file_path = os.path.join(
        DOCUMENT_TYPES_PATH,
        f"{internal_type.lower()}.json"
    )

    if not os.path.exists(file_path):
        return {}

    with open(file_path, "r") as f:
        return json.load(f)


def merge_input_groups(document_schema):
    merged = []

    # Load base type
    base_schema = load_base_type(document_schema.get("internal_type"))

    if base_schema and base_schema.get("common_input_groups"):
        for group in base_schema["common_input_groups"]:
            group["source"] = "base"
            merged.append(group)

    # Add document specific groups
    if document_schema.get("input_groups"):
        for group in document_schema["input_groups"]:
            group["source"] = "document"
            merged.append(group)

    return merged

