from loader import load_document_json

doc = load_document_json(
    department="engineering",
    document_filename="deployment_sop.json"
)

print("Resolved document loaded")
print("Name:", doc["document_name"])
print("Type:", doc["internal_type"])
print("Risk:", doc["risk_level"])
print("Approval required:", doc["approval_required"])
print("Versioning strategy:", doc["versioning_strategy"])
print("Mandatory sections:", doc["mandatory_sections"])
print("Total sections:", len(doc["sections"]))
