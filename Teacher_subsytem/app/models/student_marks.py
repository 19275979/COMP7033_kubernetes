from pydantic import BaseModel, Field
from .assessments import Assessment
from .students import Student
from datetime import datetime
from fastapi import FastAPI, UploadFile

class Results(BaseModel):
    answer_id: str  # Foreign key referencing the Answer model
    marks: float
    feedback: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    class Config:
        from_attributes = True


class Answers(BaseModel):
    assessment_id: str  # Foreign key referencing the Assessment model
    student_id: str  # Foreign key referencing the Student model
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    answer_sheet: UploadFile
    class Config:
        from_attributes = True