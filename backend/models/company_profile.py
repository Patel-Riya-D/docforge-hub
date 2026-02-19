from pydantic import BaseModel
from typing import List, Optional
from pydantic import Field


class CompanyProfile(BaseModel):
    company_name: str
    industry: str
    size: Optional[str] = None
    country: Optional[str] = None
    primary_office: Optional[str] = None
    work_model: Optional[str] = None
    working_hours: Optional[str] = None
    payroll_frequency: Optional[str] = None
    hr_system: Optional[str] = None
    remote_allowed: Optional[bool] = None
    remote_regions: List[str] = Field(default_factory=list)
    security_controls: Optional[List[str]] = Field(default_factory=list)
    data_classification_levels: Optional[List[str]] = Field(default_factory=list)
    compliance_frameworks: Optional[List[str]] = Field(default_factory=list)
