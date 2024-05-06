from typing import List
from models.classes import Classroom
from .class_schema import class_individual_serial

def material_individual_serial(material) -> dict:
    return {
            "material_id" : str(material["_id"]),
            "class_id" : material["class_id"],
            "description" : material["description"],
            "material" : material["material"],
            "upload_date" : material["upload_date"]
        }

def material_list(materials) -> list:
    return [material_individual_serial(material) for material in materials]


