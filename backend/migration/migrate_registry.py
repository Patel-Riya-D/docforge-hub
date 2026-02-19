import os
import json
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.db_models import Document

REGISTRY_PATH = "/home/riyap/DocForage/document_registry"


def migrate_documents():
    db: Session = SessionLocal()

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

            doc = Document(
                document_name=data.get("document_name"),
                department=data.get("department"),
                internal_type=data.get("internal_type"),
                risk_level=data.get("risk_level"),
                approval_required=data.get("approval_required", False),
                versioning_strategy=data.get("versioning", {}).get("review_cycle"),
                sections=data.get("sections"),
                input_groups=data.get("input_groups"),
            )

            db.add(doc)

    db.commit()
    db.close()

    print("Migration completed.")


if __name__ == "__main__":
    migrate_documents()
