"""
schema_merger.py

This module handles merging of document input schemas in the DocForge Hub system.

It combines:
- Base document type input groups (shared/common fields)
- Document-specific input groups (custom fields)

Key Features:
- Supports reusable base schemas for different document types
- Enables modular and scalable form design
- Adds source tracking for each input group (base vs document)

Purpose:
To create a unified input schema that can be rendered in the UI
for collecting user inputs before document generation.

This module helps maintain DRY (Don't Repeat Yourself) principles
by separating common and document-specific fields.
"""
import json
import os

DOCUMENT_TYPES_PATH = "/home/riyap/DocForage/document_types"

def load_base_type(internal_type: str):
    """
    Load base schema for a given document type.

    This function retrieves a JSON schema file containing
    common input groups for a specific document type.

    Args:
        internal_type (str): Document type (e.g., POLICY, SOP).

    Returns:
        dict: Base schema JSON if found, otherwise empty dict.

    Behavior:
        - Constructs file path dynamically
        - Returns parsed JSON content
        - Returns empty dict if file does not exist

    Notes:
        - Base schemas are stored in DOCUMENT_TYPES_PATH
        - Enables reuse of common input fields across documents
    """
    file_path = os.path.join(
        DOCUMENT_TYPES_PATH,
        f"{internal_type.lower()}.json"
    )

    if not os.path.exists(file_path):
        return {}

    with open(file_path, "r") as f:
        return json.load(f)


def merge_input_groups(document_schema):
    """
    Merge base and document-specific input groups into a unified schema.

    This function combines:
    1. Common input groups from base document type
    2. Custom input groups from specific document schema

    Args:
        document_schema (dict): Document schema containing:
            - internal_type (str)
            - input_groups (list)

    Returns:
        list: Merged list of input groups with source metadata.

    Workflow:
        1. Load base schema using internal_type
        2. Add base input groups (marked as "base")
        3. Add document-specific input groups (marked as "document")
        4. Return combined list

    Output Format:
        [
            {
                "name": "Group Name",
                "fields": [...],
                "source": "base" | "document"
            }
        ]

    Notes:
        - Maintains order: base groups first, then document-specific
        - Adds "source" field for traceability
        - Supports modular schema design

    Example:
        Base → "Company Info"
        Document → "Policy Details"

        Result → ["Company Info", "Policy Details"]
    """
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

