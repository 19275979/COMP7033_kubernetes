from fastapi import APIRouter, Body, HTTPException, Path, UploadFile, File, Response
from models.user import Staff, StaffLogin
from models.students import  Student
from models.classes import Class
from models.study_materials import StudyMaterial
from schema.user_schema import staff_list
from schema.student_schema import student_list
from schema.class_schema import class_list
from config.database import db, fs
from auth.jwt_handler import signJWT
from auth.auth_bearer import jwtBearer
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from gridfs import GridFS
import base64, mimetypes

router = APIRouter()
fs = GridFS(db)

staff_collection = db ["staff_collection"]
student_collection = db["student_collection"]
class_collection = db["class_collection"]
studymaterial_collection = db["studymaterial_collection"] 


# Get all staff from the database
@router.get("/staff", tags=["staff"])
async def get_staffs():
    staffs = staff_list(staff_collection.find())
    return staffs


# User Signup [Create a new user] 
@router.post("/staff/signup", tags=["staff"])
async def staff_signup(staff: Staff = Body(default=None)):
    # Check if email already exists in the database
    existing_staff = staff_collection.find_one({"email": staff.email})
    if existing_staff:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Insert staff into MongoDB collection
    staff_collection.insert_one(staff.dict())
    return signJWT(staff.email)

# User Login
@router.post("/staff/login", tags=["staff"])
async def staff_login(staff_login: StaffLogin = Body(default=None)):
    # Search for staff in MongoDB collection
    staff = staff_collection.find_one({"email": staff_login.email, "password": staff_login.password})
    if staff:
        return signJWT(staff_login.email)
    else:
        raise HTTPException(status_code=401, detail="Invalid login details")



# Get all student from the database
@router.get("/student", tags=["student"])
async def get_students():
    students = student_list(student_collection.find())
    return students


# Create a new student
@router.post("/student/insert", tags=["student"])
async def student_signup(student: Student = Body(default=None)):
    # Check if email already exists in the database
    existing_student = student_collection.find_one({"email": student.email})
    if existing_student:
        raise HTTPException(status_code=400, detail="Email already exists")
     
    # Insert student into MongoDB collection
    student_collection.insert_one(student.dict())
    return signJWT(student.email)


# Get all class from the database
@router.get("/class", tags=["class"])
async def get_class():
    classes = class_list(class_collection.find())
    return classes


# Create a new class with student IDs
@router.post("/classes/", tags=["class"])
async def create_class(class_data: Class = Body(default=None)):
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
        "module_name": class_data.module_name,
        "student": students
    }
    inserted_class = class_collection.insert_one(new_class)
    class_id = str(inserted_class.inserted_id)


    return {"id": class_id, **new_class}



#  Add students to the class
@router.post("/classes/{class_id}/students/{student_id}", tags=["class"])
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



@router.post("/upload/", tags=["studymaterial"])
async def upload_study_material(class_id: str, topic: str, material: UploadFile = File(...)):
    # Check if class exists
    class_doc = class_collection.find_one({"_id": ObjectId(class_id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Ensure only PDF files are uploaded
    if not material.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Save file to GridFS
    file_id = fs.put(material.file, filename=material.filename)
    
    # Save metadata to MongoDB
    study_material = {
        "class_id": class_id,
        "topic": topic,
        "file_id": str(file_id),
        "upload_date": datetime.utcnow()
    }
    
    # Insert metadata into study_materials collection
    db.studymaterial_collection.insert_one(study_material)
    
    return {"message": "Study material uploaded successfully"}



@router.get("/download/{file_id}", tags=["studymaterial"])
async def download_study_material(file_id: str = Path(..., title="The ID of the study material file")):
    try:
        # Validate file_id
        if not ObjectId.is_valid(file_id):
            raise HTTPException(status_code=400, detail="Invalid file ID")

        # Retrieve file from GridFS
        file_info = fs.get(ObjectId(file_id))
        if file_info is None:
            raise HTTPException(status_code=404, detail="File not found")

        # Ensure only PDF files are downloaded
        if not file_info.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files can be downloaded")

        # Read file content into memory
        file_content = file_info.read()

        # Return file content as response
        return Response(content=file_content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={file_info.filename}"})
    except HTTPException:
        # Re-raise HTTPException to return specific error responses
        raise
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail="Failed to download study material")




@router.get("/study_materials/", tags=["studymaterial"])
async def get_study_materials():
    study_materials = []
    for file_info in db.studymaterial_collection.find():
        class_id = file_info["class_id"]
        topic = file_info["topic"]
        file_id = file_info["file_id"]
        upload_date = file_info["upload_date"]

        study_materials.append({
            "class_id": str(class_id),
            "topic": topic,
            "upload_date": upload_date,
            "file_id": file_id
        })
    return study_materials

