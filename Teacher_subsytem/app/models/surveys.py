from pydantic import BaseModel, Field
from datetime import datetime
from .classes import Classroom
from typing import List

class SurveyResponse(BaseModel):
    survey_id: str 
    staff_id: str # Staff ID referencing the staff model
    response: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)

class Survey(BaseModel):
    staff_id: List[str]  # Foreign key referencing the Class model
    description: str
    survey_form: str  # Binary datatype for the exercise content
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    submission_date: datetime
    class Config:
        from_attributes = True


