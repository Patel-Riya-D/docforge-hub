"""
migration_registry.py

This module synchronizes document registry JSON files with the database.

It ensures that all document templates stored in the filesystem
are accurately reflected in the database by:
- Inserting new documents
- Updating existing documents
- Deleting obsolete documents

Key Features:
- Directory-based registry scanning
- Case-insensitive document matching
- Automatic insert/update/delete operations
- Supports structured fields (sections, input groups)

This module acts as a source-of-truth sync mechanism between:
    JSON Registry → Database

It is typically used during:
- Initial data setup
- Template updates
- Deployment or migration processes
"""
import os
import json
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import SessionLocal
from backend.db_models import Document

REGISTRY_PATH = "/home/riyap/DocForage/document_registry"


def migrate_documents():
    """
    Synchronize document registry JSON files with the database.

    This function performs a full sync between the filesystem-based
    document registry and the database.

    Workflow:
    1. Traverse registry directory (organized by department)
    2. Load all JSON document definitions
    3. For each document:
        - If exists → update fields
        - If not exists → insert new record
    4. Identify and delete documents that no longer exist in JSON
    5. Commit all changes

    Data Synced:
        - document_name
        - department
        - internal_type
        - risk_level
        - approval_required
        - versioning_strategy
        - sections
        - input_groups

    Matching Logic:
        - Case-insensitive match on (document_name, department)

    Returns:
        None

    Side Effects:
        - Inserts new records into database
        - Updates existing records
        - Deletes outdated records
        - Prints logs for each operation

    Notes:
        - REGISTRY_PATH must point to valid directory structure
        - Each department should contain JSON files
        - JSON files must follow expected schema

    Example Directory Structure:
        document_registry/
            HR/
                policy.json
                handbook.json
            IT/
                security_policy.json

    Usage:
        Run as script:
            python migration_registry.py

    Raises:
        Exception: If file reading or database operations fail.
    """
    db: Session = SessionLocal()

    print("Starting registry sync...")

    # Load all JSON files first
    json_documents = []

    for department in os.listdir(REGISTRY_PATH):
        dept_path = os.path.join(REGISTRY_PATH, department)

        if not os.path.isdir(dept_path):
            continue

        for file in os.listdir(dept_path):
            if not file.endswith(".json"):
                continue

            file_path = os.path.join(dept_path, file)

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                json_documents.append(data)

                doc_name = data.get("document_name").strip()
                dept_name = data.get("department").strip()

                existing = db.query(Document).filter(
                    func.lower(Document.document_name) == doc_name.lower(),
                    func.lower(Document.department) == dept_name.lower()
                ).first()

                if existing:
                   
                    existing.internal_type = data.get("internal_type")
                    existing.risk_level = data.get("risk_level")
                    existing.approval_required = data.get("approval_required", False)
                    existing.versioning_strategy = data.get("versioning", {}).get("review_cycle")
                    existing.sections = data.get("sections")
                    existing.input_groups = data.get("input_groups")

                    print(f"Updated: {data.get('document_name')}")

                else:
                    new_doc = Document(
                        document_name=data.get("document_name"),
                        department=data.get("department"),
                        internal_type=data.get("internal_type"),
                        risk_level=data.get("risk_level"),
                        approval_required=data.get("approval_required", False),
                        versioning_strategy=data.get("versioning", {}).get("review_cycle"),
                        sections=data.get("sections"),
                        input_groups=data.get("input_groups"),
                    )

                    db.add(new_doc)
                    print(f"Inserted: {data.get('document_name')}")

   
    db_docs = db.query(Document).all()

    for db_doc in db_docs:
        exists_in_json = any(
            db_doc.document_name.lower() == j["document_name"].lower()
            and db_doc.department.lower() == j["department"].lower()
            for j in json_documents
        )

        if not exists_in_json:
            print(f"Deleted (not in JSON anymore): {db_doc.document_name}")
            db.delete(db_doc)

    db.commit()
    db.close()

    print("Registry sync completed successfully.")


if __name__ == "__main__":
    """
    Entry point for running the registry migration script.

    Executes full synchronization of JSON registry with database.

    Usage:
        python migration_registry.py
    """
    migrate_documents()