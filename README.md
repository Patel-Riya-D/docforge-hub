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

## 📂 Project Structure

backend/
frontend/
docs/

---

## 🔐 Environment Setup

Create a `.env` file (do not commit it):

DATABASE_URL=
AZURE_OPENAI_KEY=
AZURE_OPENAI_ENDPOINT=

---

## ▶ Run Backend

uvicorn main:app --reload

---

## ▶ Run Frontend

streamlit run app.py
