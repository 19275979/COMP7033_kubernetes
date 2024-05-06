from fastapi import APIRouter, Body, HTTPException, Path, Depends
from models.classes import Classroom
from schema.class_schema import class_list
from config.database import db
from auth.jwt_handler import signJWT
from auth.auth_bearer import jwtBearer
from bson import ObjectId
from fastapi import FastAPI, UploadFile, File
from fastapi import Depends, HTTPException
from auth.jwt_handler import decodeJWT
from fastapi.security import HTTPAuthorizationCredentials

classroom = APIRouter()

student_collection = db["student_collection"]
class_collection = db["class_collection"]



async def get_user_id(credentials: str = Depends(jwtBearer(roles = ["teacher"]))):
    payload = decodeJWT(credentials)
    if payload:
        return payload.get("user_id")
    else:
        raise HTTPException(status_code=403, detail="Invalid token or expired token.")


@classroom.get("/class", tags=["class"])
async def get_all_classes(user_id: str = Depends(get_user_id)):
    # Retrieve all class documents from MongoDB
    all_classes = class_collection.find({"teacher_id": user_id}) 
    

    # Format all class documents for response
    formatted_classes = []
    for class_doc in all_classes:
        formatted_class = {
            "id": str(class_doc["_id"]),
            "module_name": class_doc["module_name"],
            "student_count": len(class_doc["student"]),
            "students": [
                {
                    "id": str(student["_id"]),
                    "name": student["name"],
                    "email": student["email"]
                }
                for student in class_doc["student"]
            ]
        }
        formatted_classes.append(formatted_class)

    return formatted_classes


# Get a particular class by ID
@classroom.get("/class/{class_id}", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["class"])
async def get_class_by_id(
    class_id: str = Path(..., title="The ID of the class")
):
    # Retrieve the class document from MongoDB
    class_doc = class_collection.find_one({"_id": ObjectId(class_id)})
    
    # Check if the class document exists
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    # Format the class document for response
    formatted_class = {
        "id": str(class_doc["_id"]),
        "module_name": class_doc["module_name"],
        "student_count": len(class_doc["student"]),
        "students": [
            {
                "id": str(student["_id"]),
                "name": student["name"],
                "email": student["email"]
            }
            for student in class_doc["student"]
        ]
    }

    return formatted_class


#  Add students to the class
@classroom.post("/class/{class_id}/student/{student_id}", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["class"])
async def add_student_to_class(
    class_id: str = Path(..., title="The ID of the class"),
    student_id: str = Path(..., title="The ID of the student")
):
    # Check if class exists
    class_doc = class_collection.find_one({"_id": ObjectId(class_id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    # Check if student exists
    student_doc = student_collection.find_one({"_id": ObjectId(student_id)})
    if not student_doc:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check if student already in class
    if student_id in class_doc["student"]:
        raise HTTPException(status_code=400, detail="Student already in class")

    # Retrieve student details
    student_details = {
        "_id": ObjectId(student_id),
        "name": student_doc["name"],
        "email": student_doc["email"]
    }

    # Update the class document to add the student ID
    result = class_collection.update_one(
        {"_id": ObjectId(class_id)},
        {"$addToSet": {"student": student_details}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Student already in class")

    return {"message": "Student added to class successfully"}


# Delete a student from the class
@classroom.delete("/class/{class_id}/student/{student_id}", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["class"])
async def remove_student_from_class(
    class_id: str = Path(..., title="The ID of the class"),
    student_id: str = Path(..., title="The ID of the student")
):
    # Check if class exists
    class_doc = class_collection.find_one({"_id": ObjectId(class_id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    # Check if student exists in the class
    if student_id not in [str(student['_id']) for student in class_doc["student"]]:
        raise HTTPException(status_code=404, detail="Student not found in class")

    # Remove the student from the class
    result = class_collection.update_one(
        {"_id": ObjectId(class_id)},
        {"$pull": {"student": {"_id": ObjectId(student_id)}}}
    )

    # Check if the update was successful
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to remove student from class")

    return {"message": "Student removed from class successfully"}







##########  STUB AND TESTING APIs ##########



@classroom.get("/user/payload", tags=["user"])
async def get_user_payload(user_id: str = Depends(get_user_id)):
    return user_id

# Create a new class with student IDs
@classroom.post("/class/new", tags=["class"])
async def create_class(class_data: Classroom = Body(default=None)):
    # Get student details for the provided student IDs
    students = []
    for student_id in class_data.student:
        student = student_collection.find_one(
            {"_id": ObjectId(student_id)},
            {"student_id": 1, "name": 1, "email": 1}  # Include student_id, name, and email
        )
        if student:
            students.append(student)
        else:
            raise HTTPException(status_code=404, detail=f"Student with ID {student_id} not found")
    # Create a new class
    new_class = {
        "teacher_id": class_data.teacher_id,
        "module_name": class_data.module_name,
        "student": students
    }
    inserted_class = class_collection.insert_one(new_class)
    class_id = str(inserted_class.inserted_id)
    return {"id": class_id, **new_class}