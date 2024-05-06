from fastapi import APIRouter, Body, HTTPException, Path
from models.students import  Student
from schema.student_schema import student_list
from config.database import db
from auth.jwt_handler import signJWT
from auth.auth_bearer import jwtBearer
from bson import ObjectId
import bcrypt

student = APIRouter()

student_collection = db["student_collection"]


# Get all student from the database
@student.get("/student", tags=["student"])
async def get_students():
    students = student_list(student_collection.find())
    return students




# student Signup [Create a new student] 
@student.post("/student/signup", tags=["student"])
async def student_signup(student: Student = Body(default=None)):
    # Check if email already exists in the database
    existing_student = student_collection.find_one({"email": student.email})
    if existing_student:
        raise HTTPException(status_code=400, detail="Email already exists")
    hashed_password = bcrypt.hashpw(student.password.encode('utf-8'), bcrypt.gensalt())
    # Insert student into MongoDB collection
    student_collection.insert_one({
        "name": student.name,
        "email": student.email,
        "password": hashed_password.decode('utf-8'),
    })
    return signJWT(student.email, "student")