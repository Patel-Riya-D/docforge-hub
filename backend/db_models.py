from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from backend.database import Base
from sqlalchemy.orm import relationship

class Draft(Base):
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(String(255))
    department = Column(String(100))
    status = Column(String(50))
    version = Column(Integer, default=1) 
    created_at = Column(DateTime, server_default=func.now())
    regeneration_count = Column(Integer, default=0)

    sections = relationship("DraftSection", back_populates="draft", cascade="all, delete")


class DraftSection(Base):
    __tablename__ = "draft_sections"

    id = Column(Integer, primary_key=True, index=True)
    draft_id = Column(Integer, ForeignKey("drafts.id", ondelete="CASCADE"))
    section_name = Column(String(255))
    section_order = Column(Integer)
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    regeneration_count = Column(Integer, default=0)

    draft = relationship("Draft", back_populates="sections") 

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(String(255))
    department = Column(String(100))
    internal_type = Column(String(100))
    risk_level = Column(String(50))
    approval_required = Column(Boolean)
    versioning_strategy = Column(String(50))
    regeneration_count = Column(Integer, default=0)
    # last_generated_at = Column(DateTime)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())

    sections = Column(JSONB)
    input_groups = Column(JSONB)


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(Integer, primary_key=True, index=True)

    company_name = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    employee_count = Column(String, nullable=True)
    regions = Column(String, nullable=True)  # store as comma-separated
    compliance_frameworks = Column(String, nullable=True)
    default_jurisdiction = Column(String, nullable=True)

    company_profile = Column(JSONB, nullable=True)