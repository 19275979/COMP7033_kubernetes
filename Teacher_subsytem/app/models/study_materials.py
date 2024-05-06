from fastapi import FastAPI, UploadFile
from pydantic import BaseModel, Field
from datetime import datetime
from .classes import Classroom

class StudyMaterial(BaseModel):
    class_id: str  # Foreign key referencing the Class model
    description: str
    material: UploadFile    #str
    upload_date: datetime =  datetime.utcnow()