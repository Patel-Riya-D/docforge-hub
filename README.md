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
## ▶ Run Backend

uvicorn main:app --reload

---

## ▶ Run Frontend

streamlit run app.py
