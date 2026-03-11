# 📡 DocForge Hub API Documentation

Base URL

```
http://localhost:8000
```

All document APIs are under:

```
/documents
```

---

# 📄 Documents API

## 1️⃣ Preview Document

Preview the document template structure from the registry.

**Endpoint**

```
POST /documents/preview
```

**Request Body**

```json
{
  "department": "engineering",
  "document_filename": "rfc"
}
```

**Response**

```json
{
  "document_name": "Request for Comments (RFC)",
  "department": "engineering",
  "sections": [
    {
      "name": "Summary",
      "mandatory": true
    }
  ]
}
```

---

## 2️⃣ Generate Document

Generate a new AI-powered document draft.

**Endpoint**

```
POST /documents/generate
```

**Request Body**

```json
{
  "department": "engineering",
  "document_filename": "rfc",
  "company_profile": {
    "company_name": "Acme Corp",
    "industry": "Technology"
  },
  "document_inputs": {
    "project_name": "AI Platform"
  }
}
```

**Response**

```json
{
  "draft_id": 1,
  "status": "draft_saved",
  "message": "Draft generated and stored successfully"
}
```

---

## 3️⃣ List Drafts

Retrieve all generated drafts.

**Endpoint**

```
GET /documents/drafts
```

**Response**

```json
[
  {
    "id": 1,
    "document_name": "Request for Comments (RFC)",
    "status": "NEEDS_REVIEW",
    "version": 1
  }
]
```

---

## 4️⃣ Delete Draft

Delete a draft from the system.

**Endpoint**

```
DELETE /documents/draft/{draft_id}
```

**Example**

```
DELETE /documents/draft/1
```

**Response**

```json
{
  "message": "Draft deleted successfully"
}
```

---

## 5️⃣ Get Draft Detail

Retrieve full draft including all sections.

**Endpoint**

```
GET /documents/draft/{draft_id}
```

**Example**

```
GET /documents/draft/1
```

**Response**

```json
{
  "id": 1,
  "document_name": "Request for Comments (RFC)",
  "status": "NEEDS_REVIEW",
  "version": 1,
  "sections": [
    {
      "section_name": "Summary",
      "blocks": [],
      "status": "draft"
    }
  ]
}
```

---

## 6️⃣ List Documents

List available documents for a department.

**Endpoint**

```
GET /documents/list
```

**Query Parameter**

```
department=engineering
```

**Example**

```
GET /documents/list?department=engineering
```

**Response**

```json
[
  {
    "document_name": "Request for Comments (RFC)",
    "internal_type": "policy"
  }
]
```

---

## 7️⃣ Export Draft

Export a document draft into a file format.

**Endpoint**

```
GET /documents/export/{draft_id}/{file_type}
```

**Example**

```
GET /documents/export/1/docx
```

**Supported Formats**

* docx (Microsoft Word)
* pdf (PDF Document)
* xls (Excel Spreadsheet)

⚠️ All sections must be **approved** before exporting.

---

## 8️⃣ Create Company Profile

Store company profile information.

**Endpoint**

```
POST /documents/company-profile
```

**Request**

```json
{
  "company_name": "Acme Corp",
  "industry": "Technology"
}
```

**Response**

```json
{
  "id": 1,
  "company_name": "Acme Corp",
  "industry": "Technology"
}
```

---

## 9️⃣ Approve Section

Approve a generated section before exporting.

**Endpoint**

```
POST /documents/approve-section
```

**Parameters**

```
draft_id
section_name
```

**Example**

```
draft_id=1
section_name=Summary
```

**Response**

```json
{
  "message": "Section approved successfully",
  "section_name": "Summary",
  "status": "approved"
}
```

---

## 🔟 Regenerate Section

Regenerate a section using AI with improvement instructions.

**Endpoint**

```
POST /documents/regenerate-section
```

**Parameters**

```
draft_id
section_name
improvement_note
```

**Example**

```
draft_id=1
section_name=Summary
improvement_note=Make the explanation clearer
```

**Response**

```json
{
  "message": "Section regenerated successfully"
}
```

---

## 1️⃣1️⃣ Save Section Edit

Save manual edits for a section.

**Endpoint**

```
POST /documents/save-section-edit
```

**Request Body**

```json
{
  "draft_id": 1,
  "section_name": "Summary",
  "updated_text": "Updated section content..."
}
```

**Response**

```json
{
  "message": "Section updated and improved successfully"
}
```

---

## 1️⃣2️⃣ Generate Clarification Questions

Generate AI-based clarification questions when required inputs are missing.

**Endpoint**

```
POST /documents/generate-questions
```

**Request Body**

```json
{
  "department": "engineering",
  "document_filename": "rfc",
  "company_profile": {},
  "document_inputs": {}
}
```

**Response**

```json
{
  "questions": [
    {
      "question": "What problem does this RFC address?",
      "field": "problem_statement"
    }
  ]
}
```

---

## 1️⃣3️⃣ Publish to Notion

Publish a finalized document to Notion.

**Endpoint**

```
POST /documents/publish-notion/{draft_id}
```

**Example**

```
POST /documents/publish-notion/1
```

**Response**

```json
{
  "message": "Published to Notion successfully"
}
```

---

# 📘 Interactive API Docs

Swagger UI

```
http://localhost:8000/docs
```


