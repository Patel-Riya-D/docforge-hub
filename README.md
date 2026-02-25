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

## Wireframe 

![Wireframe Step 1](https://github.com/Patel-Riya-D/docforge-hub/blob/feature/project-setup/wireframe/main.png)
---
![Wireframe Step 2](https://github.com/Patel-Riya-D/docforge-hub/blob/feature/project-setup/wireframe/step2.png)
---
![Wireframe Step 2](https://github.com/Patel-Riya-D/docforge-hub/blob/feature/project-setup/wireframe/library.png)
---
## ▶ Run Backend

uvicorn main:app --reload

---

## ▶ Run Frontend

streamlit run app.py
