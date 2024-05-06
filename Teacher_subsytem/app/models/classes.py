from pydantic import BaseModel
from typing import List
#from models.students import Student

class Classroom(BaseModel):
    teacher_id: str
    module_name: str
    student: List[str] = []  # List of students IDs