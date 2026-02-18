company_block = ""
if company_profile:
    company_block = f"""
    Company Name: {company_profile.get('company_name')}
    Industry: {company_profile.get('industry')}
    Employee Count: {company_profile.get('employee_count')}
    Regions: {", ".join(company_profile.get('regions', []))}
    Compliance: {", ".join(company_profile.get('compliance_frameworks', []))}
    Jurisdiction: {company_profile.get('default_jurisdiction')}
    """

inputs_block = ""
if document_inputs:
    for key, value in document_inputs.items():
        inputs_block += f"{key}: {value}\n"

context = {
    "document_name": registry_doc["document_name"],
    "document_type": registry_doc["internal_type"],
    "risk_level": registry_doc["risk_level"],
    "section_name": section["name"],
    "company_profile": company_block,
    "document_inputs": inputs_block,
}
