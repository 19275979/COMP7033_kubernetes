from pydantic import BaseModel, Field
from datetime import datetime
from .classes import Classroom
from fastapi import FastAPI, UploadFile

class Assessment(BaseModel):
    #exam id
    class_id: str  # Foreign key referencing the Class model
    topic: str
    exercise_data: UploadFile  # Binary datatype for the exercise content
    upload_date: datetime
    submission_date: datetime
    max_marks: int
    class Config:
        from_attributes = True
