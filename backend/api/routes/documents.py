from fastapi import APIRouter, HTTPException
from backend.api.schemas import DocumentPreviewRequest
from backend.models.company_profile import CompanyProfile
from backend.db_models import CompanyProfile
from backend.api.schemas import CompanyProfileCreate
from backend.generation.question_engine import generate_clarification_questions
from backend.registry.db_loader import load_document_from_db
from backend.generation.generator import generate_draft
from backend.api.schemas import DocumentGenerateRequest
from backend.api.schemas import QuestionRequest
from sqlalchemy.orm import Session
from fastapi import Depends
from backend.dependencies import get_db
from backend.db_models import Draft, DraftSection
from backend.db_models import Document
from datetime import datetime, timezone
from fastapi.responses import StreamingResponse
from backend.export.exporter import generate_docx, generate_pdf, generate_xls
from backend.export.docx_formatter import build_docx
import io
from sqlalchemy import func
import json
from pydantic import BaseModel
from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from backend.integrations.notion_publisher import publish_document_to_notion
from backend.rag.query_search_engine import answer_question
from backend.rag.compare_engine import compare_documents
from backend.rag.summarizer import summarize_document
from backend.rag.evaluate import run_evaluation

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/preview")
def preview_document(
    payload: DocumentPreviewRequest,
    db: Session = Depends(get_db)
):
    try:
        doc = load_document_from_db(
            db=db,
            department=payload.department,
            document_filename=payload.document_filename
        )
        return doc

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
def generate_document(
    payload: DocumentGenerateRequest,
    db: Session = Depends(get_db)
):
    try:
        registry_doc = load_document_from_db(
            db=db,
            department=payload.department,
            document_filename=payload.document_filename
        )

        # 🔎 Validate that all inputs are filled before generating
        for key, value in payload.document_inputs.items():
            if value in ["", None]:
                return {
                    "status": "questions_required",
                    "message": f"Missing value for {key}"
                }
        
        draft_result = generate_draft(
            registry_doc=registry_doc,
            department=payload.department,
            document_filename=payload.document_filename,
            company_profile=payload.company_profile,
            document_inputs=payload.document_inputs,
            user_notes=getattr(payload, "user_notes", None)
        )

        latest_version = db.query(func.max(Draft.version)).filter(
            Draft.document_name == registry_doc["document_name"],
            Draft.department == payload.department
        ).scalar()

        next_version = int(latest_version or 0) + 1

        draft = Draft(
            document_name=registry_doc["document_name"],
            department=payload.department,
            document_type=registry_doc.get("internal_type"),
            industry=payload.company_profile.get("industry"),
            tags=["docforge"],
            created_by=payload.company_profile.get("company_name"),
            status=draft_result["status"],
            version=next_version,
            regeneration_count=draft_result["generation_metadata"].get("retry_count", 0)
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

        import json

        print("SECTIONS STRUCTURE:", draft_result["sections"])
        # print("DOCUMENT INPUTS RECEIVED:", payload.document_inputs)

        for idx, section in enumerate(draft_result.get("sections", []), start=1):

            print("SECTION ITEM TYPE:", type(section))

            # Convert string section to dict if needed
            if isinstance(section, str):
                try:
                    section = json.loads(section)
                except Exception:
                    continue

            if not isinstance(section, dict):
                continue

            blocks = section.get("blocks", [])

            # Ensure blocks is a list
            if isinstance(blocks, str):
                try:
                    blocks = json.loads(blocks)
                except Exception:
                    blocks = []

            if not isinstance(blocks, list):
                blocks = []
            
            section_name = str(
                section.get("name") or section.get("section_name") or "Section"
            ).strip()

            db_section = DraftSection(
                draft_id=draft.id,
                section_name=section.get("name") or section.get("section_name", "Section"),
                section_order=idx,
                content=blocks
            )

            db.add(db_section)

        db.commit()

        return {
            "draft_id": draft.id,
            "status": "draft_saved",
            "message": "Draft generated and stored successfully"
        }

    except Exception as e:
        db.rollback()
        print("GENERATE ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drafts")
def list_drafts(db: Session = Depends(get_db)):
    drafts = db.query(Draft).all()

    return [
        {
            "id": d.id,
            "document_name": d.document_name,
            "status": d.status,
            "version": d.version
        }
        for d in drafts
    ]

@router.delete("/draft/{draft_id}")
def delete_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = db.query(Draft).filter(Draft.id == draft_id).first()

    if not draft:
     raise HTTPException(status_code=404, detail="Draft not found")


    db.delete(draft)
    db.commit()

    return {"message": "Draft deleted successfully"}

@router.get("/list")
def list_documents(department: str, db: Session = Depends(get_db)):
    docs = db.query(Document).filter(func.lower(Document.department) == department.lower()).all()

    return [
        {
            "document_name": d.document_name,
            "internal_type": d.internal_type
        }
        for d in docs
    ]

@router.get("/draft/{draft_id}")
def get_draft_detail(draft_id: int, db: Session = Depends(get_db)):

    draft = db.query(Draft).filter(Draft.id == draft_id).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    sections = (
        db.query(DraftSection)
        .filter(DraftSection.draft_id == draft_id)
        .order_by(DraftSection.section_order.asc())
        .all()
    )

    return {
        "id": draft.id,
        "document_name": draft.document_name,
        "status": draft.status,
        "version": draft.version,
        "sections": [
            {
                "section_name": s.section_name,
                "blocks": s.content,
                "status": s.status,
                "regeneration_count": s.regeneration_count
            }
            for s in sections
        ]
    }

@router.get("/export/{draft_id}/{file_type}")
def export_draft(draft_id: int, file_type: str, db: Session = Depends(get_db)):

    draft_obj = db.query(Draft).filter(Draft.id == draft_id).first()

    if not draft_obj:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    not_approved = db.query(DraftSection).filter(
        DraftSection.draft_id == draft_id,
        DraftSection.status != "approved"
    ).count()

    if not_approved > 0:
        raise HTTPException(
            status_code=400,
            detail="All sections must be approved before export"
        )

    sections = (
        db.query(DraftSection)
        .filter(DraftSection.draft_id == draft_id)
        .order_by(DraftSection.section_order.asc())
        .all()
    )

    # Fetch original document metadata
    doc_meta = db.query(Document).filter(
        func.lower(Document.document_name) == draft_obj.document_name.lower(),
        func.lower(Document.department) == draft_obj.department.lower()
    ).first()

    internal_type = doc_meta.internal_type if doc_meta else ""
    risk_level = doc_meta.risk_level if doc_meta else "MEDIUM"

    sections_data = []

    for s in sections:

        blocks = s.content

        if isinstance(blocks, str):
            try:
                blocks = json.loads(blocks)
            except:
                blocks = [{"type": "paragraph", "content": blocks}]

        elif isinstance(blocks, dict):
            blocks = [blocks]

        elif not isinstance(blocks, list):
            blocks = []

        sections_data.append({
            "name": s.section_name,
            "blocks": blocks,
            "mandatory": True
        })

        draft_dict = {
            "source_document": {
                "document_name": draft_obj.document_name,
                "department": draft_obj.department,
                "internal_type": internal_type,
                "risk_level": risk_level
            },
            "version": f"v{draft_obj.version}",
            "status": draft_obj.status,
            "generation_metadata": {
                "generated_at": draft_obj.created_at.isoformat() if draft_obj.created_at else ""
            },
            "sections": sections_data
        }
    filename = draft_obj.document_name.replace(" ", "_")

    if file_type == "docx":
        print("SECTIONS SENT TO DOCX:", draft_dict["sections"])
        docx_bytes = build_docx(draft_dict)

        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}.docx"'}
        )

    elif file_type == "pdf":
        buffer = generate_pdf(draft_obj)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'}
        )

    elif file_type == "xls":
        buffer = generate_xls(draft_obj)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}.xlsx"'}
        )

    else:
        raise HTTPException(status_code=400, detail="Invalid export type")

@router.post("/company-profile")
def create_company_profile(profile: CompanyProfileCreate, db: Session = Depends(get_db)):
    db_profile = CompanyProfile(**profile.model_dump())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.post("/approve-section")
def approve_section(
    draft_id: int,
    section_name: str,
    db: Session = Depends(get_db)
):
    section = db.query(DraftSection).filter(
        DraftSection.draft_id == draft_id,
        DraftSection.section_name == section_name
    ).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    if section.status == "approved":
        return {"message": "Section already approved"}

    section.status = "approved"
    section.approved_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": "Section approved successfully",
        "section_name": section.section_name,
        "status": section.status
    }

@router.post("/regenerate-section")
def regenerate_section(
    draft_id: int,
    section_name: str,
    improvement_note: str,
    db: Session = Depends(get_db)
):
    draft = db.query(Draft).filter(Draft.id == draft_id).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    section = db.query(DraftSection).filter(
        DraftSection.draft_id == draft_id,
        DraftSection.section_name == section_name
    ).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    try:
        from backend.generation.generator import regenerate_section_llm
        import json

        # Normalize existing content
        blocks = section.content

        if isinstance(blocks, str):
            try:
                blocks = json.loads(blocks)
            except:
                blocks = []

        if not isinstance(blocks, list):
            blocks = []

        # Call LLM regeneration
        new_blocks = regenerate_section_llm(
            draft={
                "source_document": {
                    "internal_type": draft.document_name,
                    "risk_level": "MEDIUM",
                    "department": draft.department
                }
            },
            section={
                "name": section.section_name,
                "blocks": blocks
            },
            issues=[f"User correction: {improvement_note}"]
        )

        # Ensure result is always list
        if isinstance(new_blocks, dict):
            new_blocks = [new_blocks]

        if not isinstance(new_blocks, list):
            new_blocks = [
                {
                    "type": "paragraph",
                    "content": str(new_blocks)
                }
            ]

        section.content = new_blocks
        section.status = "draft"
        section.regeneration_count += 1
        draft.status = "NEEDS_REVIEW"

        db.commit()

        return {"message": "Section regenerated successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


class SaveSectionEditRequest(BaseModel):
    draft_id: int
    section_name: str
    updated_text: str


@router.post("/save-section-edit")
def save_section_edit(
    payload: SaveSectionEditRequest,
    db: Session = Depends(get_db)
):
    draft = db.query(Draft).filter(Draft.id == payload.draft_id).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    section = db.query(DraftSection).filter(
        DraftSection.draft_id == payload.draft_id,
        DraftSection.section_name == payload.section_name
    ).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    try:
        # -------------------------------
        # 🔹 Step 1: Improve grammar using LLM
        # -------------------------------

                # Detect document type
        doc_meta = db.query(Document).filter(
            func.lower(Document.document_name) == draft.document_name.lower(),
            func.lower(Document.department) == draft.department.lower()
        ).first()

        document_type = doc_meta.internal_type if doc_meta else ""

        # Skip LLM editing for FORM documents
        if document_type.upper() == "FORM":
            improved_text = payload.updated_text
        else:
            llm = get_llm()

            prompt = f"""
        Improve the grammar, clarity, and professionalism of the following text.

        Rules:
        - Do NOT change meaning.
        - Do NOT add new information.
        - Do NOT remove important content.
        - Return only the improved version.
        - Keep enterprise tone.

        Text:
        {payload.updated_text}
        """

            response = llm.invoke([
                SystemMessage(content="You are a professional enterprise document editor."),
                HumanMessage(content=prompt)
            ])

            improved_text = response.content.strip()


        # -------------------------------
        # 🔹 Step 2: Replace paragraph block
        # -------------------------------

        blocks = section.content or []

        if not isinstance(blocks, list):
            blocks = []

        new_blocks = []
        paragraph_found = False

        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "paragraph":
                paragraph_found = True
                new_blocks.append({
                    "type": "paragraph",
                    "content": improved_text
                })
            else:
                new_blocks.append(block)

        if not paragraph_found:
            new_blocks.append({
                "type": "paragraph",
                "content": improved_text
            })

        # -------------------------------
        # 🔹 Step 3: Save
        # -------------------------------

        section.content = new_blocks
        section.status = "draft"
        draft.status = "NEEDS_REVIEW"

        db.commit()
        db.refresh(section)

        return {"message": "Section updated and improved successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-questions")
def generate_questions(
    payload: QuestionRequest,
    db: Session = Depends(get_db)
):

    registry_doc = load_document_from_db(
        db=db,
        department=payload.department,
        document_filename=payload.document_filename
    )

    if not registry_doc:
        return {"questions": []}

    questions = generate_clarification_questions(
        registry_doc=registry_doc,
        company_profile=payload.company_profile,
        document_inputs=payload.document_inputs
    )

    return {"questions": questions}

@router.post("/publish-notion/{draft_id}")
def publish_to_notion(draft_id: int, db: Session = Depends(get_db)):

    draft = db.query(Draft).filter(Draft.id == draft_id).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    sections = (
        db.query(DraftSection)
        .filter(DraftSection.draft_id == draft_id)
        .order_by(DraftSection.section_order.asc())
        .all()
    )

    if not sections:
        raise HTTPException(status_code=404, detail="Draft sections not found")

    sections_data = []

    for s in sections:

        blocks = s.content

        if isinstance(blocks, str):
            try:
                blocks = json.loads(blocks)
            except:
                blocks = []

        if not isinstance(blocks, list):
            blocks = []

        sections_data.append({
            "name": s.section_name,
            "blocks": blocks
        })

    doc_meta = db.query(Document).filter(
        func.lower(Document.document_name) == draft.document_name.lower(),
        func.lower(Document.department) == draft.department.lower()
    ).first()

    document_type = (doc_meta.internal_type.title() if doc_meta and doc_meta.internal_type else "Policy")
    company = db.query(CompanyProfile).first()
    company_name = company.company_name if company else "DocForge"
    industry = company.industry if company else "SaaS"

    print("DOC TYPE:", document_type)
    print("INDUSTRY:", industry)
    print("COMPANY:", company_name)

    print("DOCUMENT TYPE SENT TO NOTION:", document_type)

    publish_document_to_notion(
        document_name=draft.document_name,
        sections=sections_data,
        version=int(draft.version),
        document_type=document_type,
        industry=industry,
        tags=[draft.department],
        created_by=company_name,
        created_at=str(draft.created_at)
    )

    return {"message": "Published to Notion successfully"}

@router.post("/rag-query")
def rag_query(data: dict):

    question = data.get("question")

    filters = {
        "doc_type": data.get("doc_type"),
        "industry": data.get("industry")
    }

    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    result = answer_question(question,filters)

    return result

@router.post("/rag-compare")
def rag_compare(data: dict):

    doc_a = data.get("doc_a")
    doc_b = data.get("doc_b")
    topic = data.get("topic", "")

    if not doc_a or not doc_b:
        raise HTTPException(status_code=400, detail="doc_a and doc_b required")

    return compare_documents(doc_a, doc_b, topic)

@router.post("/rag-summarize")
def rag_summarize(data: dict):

    query = data.get("query")

    filters = {
        "doc_type": data.get("doc_type"),
        "industry": data.get("industry")
    }

    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    return summarize_document(query, filters)

@router.post("/rag-evaluate")
def rag_evaluate():

    df = run_evaluation()

    return {
        "message": "Evaluation completed",
        "data": df.to_dict(orient="records"),
        "avg_faithfulness": float(df["faithfulness"].mean()),
        "avg_relevancy": float(df["answer_relevancy"].mean())
    }