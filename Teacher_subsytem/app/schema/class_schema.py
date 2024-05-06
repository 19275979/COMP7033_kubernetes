from typing import List
from models.students import Student
from .student_schema import individual_serial as student_individual_serial

def class_individual_serial(classroom) -> dict:
    return {
        "teacher_id": classroom["teacher_id"],
        "module_id": str(classroom["_id"]),
        "module_name": classroom["module_name"],
        "student": [student_individual_serial(student) for student in classroom["student"]]
    }

def class_list(classrooms) -> list:
    return [class_individual_serial(classroom) for classroom in classrooms]


