import json
import os

BASE_PATH = "backend/generated_docs"

def save_draft(draft: dict):
    os.makedirs(BASE_PATH, exist_ok=True)
    file_path = os.path.join(BASE_PATH, f"draft_{draft['draft_id']}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(draft, f, indent=2)
