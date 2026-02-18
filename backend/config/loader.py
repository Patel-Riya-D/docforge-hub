import json
import os


def load_company_profile():
    base_path = os.path.dirname(__file__)
    path = os.path.join(base_path, "company_profile.json")

    if not os.path.exists(path):
        return {}

    with open(path, "r") as f:
        return json.load(f)
