from fastapi import APIRouter, HTTPException
from backend.api.schemas import DocumentPreviewRequest
from backend.models.company_profile import CompanyProfile
from backend.api.schemas import CompanyProfileCreate
from backend.registry.db_loader import load_document_from_db
from backend.generation.generator import generate_draft
from backend.api.schemas import DocumentGenerateRequest
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

        draft_result = generate_draft(
            registry_doc=registry_doc,
            department=payload.department,
            document_filename=payload.document_filename,
            company_profile=payload.company_profile,
            document_inputs=payload.document_inputs,
            user_notes=payload.user_notes
        )

        draft = Draft(
            document_name=registry_doc["document_name"],
            department=payload.department,
            status=draft_result["status"],  
            version=1,     
            regeneration_count=draft_result["generation_metadata"].get("retry_count", 0),      
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

        for idx, section in enumerate(draft_result["sections"], start=1):
            db_section = DraftSection(
                draft_id=draft.id,
                section_name=section["name"],
                section_order=idx,
                content=section["content"]
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
                "content": s.content
            }
            for s in sections
        ]
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

        improved_content = regenerate_section_llm(
            draft={
                "source_document": {
                    "internal_type": draft.document_name,
                    "risk_level": "MEDIUM",
                    "department": draft.department
                }
            },
            section={
                "name": section.section_name,
                "content": section.content
            },
            issues=[improvement_note]
        )

        section.content = improved_content
        section.regeneration_count += 1

        draft.status = "NEEDS_REVIEW"

        db.commit()

        return {"message": "Section regenerated successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{draft_id}/{file_type}")
def export_draft(draft_id: int, file_type: str, db: Session = Depends(get_db)):

    draft_obj = db.query(Draft).filter(Draft.id == draft_id).first()

    if not draft_obj:
        raise HTTPException(status_code=404, detail="Draft not found")

    sections = (
        db.query(DraftSection)
        .filter(DraftSection.draft_id == draft_id)
        .order_by(DraftSection.section_order.asc())
        .all()
    )

    # Fetch original document metadata
    doc_meta = db.query(Document).filter(
        Document.document_name == draft_obj.document_name,
        Document.department == draft_obj.department
    ).first()

    internal_type = doc_meta.internal_type if doc_meta else ""
    risk_level = doc_meta.risk_level if doc_meta else "MEDIUM"

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
        "sections": [
            {
                "name": s.section_name,
                "content": s.content,
                "mandatory": True
            }
            for s in sections
        ]
    }

    filename = draft_obj.document_name.replace(" ", "_")

    if file_type == "docx":
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
