# 📘 DocForge Hub

AI-powered Enterprise Document Automation Platform

DocForge Hub is a SaaS-based platform that automates enterprise document creation using Large Language Models (LLMs).
It enables organizations to generate structured, compliant, and professional business documents such as policies, PRDs, SOPs, and internal documentation with minimal manual effort.

The platform combines AI-powered content generation, structured document schemas, and human-in-the-loop validation to produce high-quality documents efficiently.

## 🚀 Overview

Organizations spend significant time drafting and maintaining internal documents.
DocForge Hub solves this by providing a structured AI-assisted document generation workflow.

Users select a document type, provide company information, and the platform generates a complete structured document section-by-section using AI.

The system ensures:

- Consistent document structure

- Context-aware content generation

- Controlled human review

- Easy document publishing and export

---

## 🚀 Key Feature

🤖 AI Section-Based Generation:

- Generates documents section-by-section
- Uses context-aware prompts including:
- Document type
- Industry
- Compliance requirements
- Risk level
- Enforces validation rules and word limits
- Maintains consistent professional formatting

🧠 Dynamic Question Generation

DocForge Hub automatically detects missing information required for a document.

The system:

- Analyzes document schemas
- Identifies critical missing inputs
- Generates clarification questions dynamically
- Ensures the document contains complete and relevant information
- This significantly improves AI output accuracy.

🧩 Document Registry System

All documents are defined using a schema-based registry system.

Each document definition includes:

- Document metadata
- Required inputs
- Section structure
- Validation rules
- Industry tags

This allows new document types to be added without modifying core code.

🧠 Human-in-the-Loop Workflow

- Review each section before finalization
- Approve, edit, or regenerate sections
- Only approved sections are included in final DOCX
- Prevents unsafe auto-publication

📊 Structured Table Rendering

- JSON-based table block structure
- Automatic duplicate row removal
- Clean DOCX table rendering
- Special handling for:
      - Revision History
      - Acknowledgement / Signature blocks

📤 Notion Integration

Generated documents can be published directly to Notion.

This enables:

- Knowledge base integration
- Documentation sharing across teams
- Centralized document management

📄 Professional DOCX Export

- Structured title page
- Proper section headings
- Bullet formatting for Definitions
- Grid-based table styling
- Signature layout formatting

---

## 🏗 Tech Stack

Backend:
- FastAPI
- PostgreSQL
- SQLAlchemy
- Azure OpenAI
- LangChain (LLM integration)

Frontend:
- Streamlit

Integrations:

- Notion API
- Azure OpenAI

---

## 📊 Database Design

The platform uses a structured database to manage:

- Document registries
- Section definitions
- Generated drafts
- Version history
- Regeneration logs
- User inputs

## Architecture

```

Streamlit Frontend
        │
        ▼
FastAPI Backend
        │
        ▼
Document Generation Engine
        │
        ▼
PostgreSQL Database
        │
        ▼
Azure OpenAI (LLM)

```
---

## 🔄 Document Generation Flow

1️⃣ User selects Department and Document Type

2️⃣ Backend loads the document schema from the registry

3️⃣ System detects missing inputs

4️⃣ AI generates clarification questions

5️⃣ User provides answers

6️⃣ AI generates document section-by-section

7️⃣ Sections are stored and reviewed by the user

8️⃣ Final document can be:

    - Exported as DOCX

    - Published to Notion

---

## Wireframe 

![Wireframe Step 1](https://github.com/Patel-Riya-D/docforge-hub/blob/feature/project-setup/wireframe/main.png)

---

![Wireframe Step 2](https://github.com/Patel-Riya-D/docforge-hub/blob/feature/project-setup/wireframe/step2.png)

---

![Wireframe Step 2](https://github.com/Patel-Riya-D/docforge-hub/blob/feature/project-setup/wireframe/library.png)

---

## ER Diagram

![ER Diagram](https://github.com/Patel-Riya-D/docforge-hub/blob/feature/project-setup/wireframe/phase1.drawio.png)

## ▶ Run Backend

uvicorn main:app --reload

---

## ▶ Run Frontend

streamlit run app.py
