# 📘 DocForge Hub

AI-powered Enterprise Document Automation Platform

## 🚀 Overview

DocForge Hub is a SaaS-based system designed to automate enterprise document drafting using Azure OpenAI.

It provides:
- Document registry management
- AI-generated structured drafts
- Section-level storage
- Version tracking
- Regeneration tracking
- Export to DOCX / PDF / XLS

---

## 🚀 Key Feature

🤖 AI Section-Based Generation:

- Generates documents section-by-section
- Context-aware prompts (document type, risk level, industry, compliance)
- Enforced word limits and validation rules

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

Frontend:
- Streamlit

---

## Architecture
Streamlit UI
      ↓
FastAPI Backend
      ↓
PostgreSQL Database
      ↓
Azure OpenAI (LLM)

---

## Flow

- User selects Department & Document

- Backend loads document template from DB

- Section-by-section prompt generation

- Azure OpenAI generates structured content

- Draft saved in database

- User can:

   - Preview full document

   - Regenerate specific sections

Download as DOCX / PDF / XLS

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
