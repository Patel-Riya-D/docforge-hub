# 📘 Phase 1 - DocForge Hub

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

## 🔎 Phase 2 - CiteRAG Lab (RAG Sandbox)

CiteRAG Lab is an advanced Retrieval-Augmented Generation (RAG) module built within DocForge Hub. It enables intelligent querying over company documents stored in Notion, providing grounded answers with citations, confidence scoring, and evaluation.

---

### 🚀 Key Features

- 🔍 **Semantic Search (RAG Pipeline)**
  - Retrieves relevant document chunks using FAISS vector search
  - Generates answers grounded strictly in retrieved context

- 🧠 **Query Refinement**
  - Improves user queries using LLM for better retrieval accuracy

- 📚 **Citations**
  - Provides traceable sources in the format:
    ```
    Document Title → Section
    ```

- 🎯 **Metadata Filtering**
  - Filter results by:
    - Document Type
    - Industry

- ⚡ **Redis Caching**
  - Caches RAG responses to improve performance and reduce LLM calls

- 📊 **Confidence Scoring**
  - Assigns reliability level (HIGH / MEDIUM / LOW)
  - Based on vector similarity scores

- 🛠️ **Multi-Tool Support**
  - 🔎 Search → Ask questions over documents
  - 🧠 Query Refiner → Improves user queries 
  - 📘 Compare → Compare two documents
  - 📝 Summarize → Generate concise summaries

- 📈 **Evaluation (RAGAS)**
RAGAS is used for standardized evaluation, complemented by custom confidence scoring based on vector similarity to improve interpretability.
  - Measures:
    - Faithfulness
    - Answer Relevancy
    - Context Precision
    - Context Recall

---

### 🧠 System Architecture

```
User Query (UI)
      │
      ▼
API Endpoint (/rag-query)
      │
      ▼
Query Refinement (LLM)
      │
      ▼
Cache Key Generation
      │
      ▼
Redis Cache Check
   ┌───────────────┐
   │ Cache HIT     │────────────> Return Response
   └───────────────┘
      │
      ▼
Cache MISS 
      │
      ▼
FAISS Vector Search (with metadata filters)
      │
      ▼
Top-K Relevant Chunks Retrieved
      │
      ▼
Context Construction
(combine chunks)
      │
      ▼
Answer Generation (LLM)
(grounded prompt)
      │
      ▼
Confidence Score Calculation
      │
      ▼
Citations Extraction
(doc title + section)
      │
      ▼
Store in Redis Cache
      │
      ▼
Return Response to UI

```

---

### 🛠️ Tech Stack

- **Backend:** FastAPI  
- **Frontend:** Streamlit  
- **Vector DB:** FAISS  
- **LLM:** Azure OpenAI  
- **Cache:** Redis  
- **Data Source:** Notion API  

---

### 📊 Example Output

- **Refined Query:**  
  _"What are the official working hours for remote employees?"_

- **Answer:**  
  _Remote employees must follow core working hours from Monday to Friday, 10:00 AM to 4:00 PM._

- **Confidence:**  
  Confidence score: 63%

- **Sources:**  
  - Remote Work Policy → Work Hours & Availability  
  - Remote Work Policy → Remote Work Agreement  

---

### 🧩 Highlights

- End-to-end RAG pipeline with real-world enterprise use case  
- Combines black-box (RAGAS) and white-box (confidence scoring) evaluation  
- Optimized for performance using Redis caching  
- Designed for explainability with citations and retrieved context  

---




















































## ▶ Run Backend

uvicorn main:app --reload

---

## ▶ Run Frontend

streamlit run app.py
