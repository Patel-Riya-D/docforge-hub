import os

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../")
)

DOCUMENT_REGISTRY_PATH = os.path.join(BASE_DIR, "document_registry")


def load_registry():
    """
    Dynamically load all departments and their documents
    from the document_registry folder.
    """
    registry = {}

    for department in os.listdir(DOCUMENT_REGISTRY_PATH):
        dept_path = os.path.join(DOCUMENT_REGISTRY_PATH, department)

        if not os.path.isdir(dept_path):
            continue

        files = [
            file for file in os.listdir(dept_path)
            if file.endswith(".json")
        ]

        if files:
            registry[department.upper()] = sorted(files)

    return registry

