from fastapi import APIRouter, Body, HTTPException, Path, Depends
from models.assessments import Assessment
from schema.assessment_schema import assessment_list, assessment_individual_serial
from config.database import db
from auth.jwt_handler import signJWT
from auth.auth_bearer import jwtBearer
from bson import ObjectId
from fastapi import FastAPI, UploadFile, File
from datetime import datetime
from gridfs import GridFS
from fastapi.responses import Response
from bson import ObjectId
import mimetypes

assessment = APIRouter()
fs = GridFS(db)

class_collection = db["class_collection"]
#student_collection = db["student_collection"]
assessment_collection = db["assessment_collection"]



@assessment.get("/assessment/download/{assessment_id}", dependencies=[Depends(jwtBearer(roles = ["teacher", "student"]))], tags=["assessment"])
async def download_exercise_data(assessment_id: str):
    try:
        # Find the assessment document based on the provided assessment_id
        assessment_document = assessment_collection.find_one({"_id": ObjectId(assessment_id)})
        
        # Check if the assessment document exists
        if assessment_document is None:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Retrieve exercise data from GridFS using the file ID stored in the assessment document
        file_info = fs.get(ObjectId(assessment_document["exercise_data"]))
        
        # Check if the file info exists
        if file_info is None:
            raise HTTPException(status_code=404, detail="Exercise data not found")
        
        # Determine media type based on file extension
        filename = file_info.filename
        media_type, _ = mimetypes.guess_type(filename)
        if media_type is None:
            media_type = "application/octet-stream"
        
        # Read file content into memory
        file_content = file_info.read()
        
        # Return file content as response
        return Response(content=file_content, media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})
    
    except HTTPException:
        # Re-raise HTTPException to return specific error responses
        raise
    
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail="Failed to download exercise data")


# GET all assessments for a class from the database
@assessment.get("/assessments/{class_id}", dependencies=[Depends(jwtBearer(roles = ["teacher", "student"]))], tags=["assessment"])
async def get_assessments(class_id: str):
    try:

        # Query assessments by class_id
        assessments = assessment_collection.find({"class_id": class_id})

        # Serialize assessments into the desired format using assessment_list
        serialized_assessments = assessment_list(assessments)

        return serialized_assessments
    except Exception as e:
        # Handle any exceptions, e.g., if ObjectId conversion fails or query encounters an error
        raise HTTPException(status_code=500, detail="Internal Server Error")

@assessment.get("/assessments/{assessment_id}", dependencies=[Depends(jwtBearer(roles = ["teacher", "student"]))], tags=["assessment"])
async def get_assessment_by_id(assessment_id: str):
    try:
        assessment_id = ObjectId(assessment_id)
        # Retrieve the assessment document from MongoDB
        assessment_doc = assessment_collection.find_one({"_id": assessment_id})
        
        if assessment_doc:
            #print(assessment_doc)
            serialized_assessment = assessment_individual_serial(assessment_doc)
            return serialized_assessment
        else:
            raise HTTPException(status_code=404, detail="Assessment not found")

    except Exception as e:
        # Handle any exceptions, e.g., if ObjectId conversion fails or query encounters an error
        raise HTTPException(status_code=500, detail="Internal Server Error")



@assessment.delete("/assessments/delete/{assessment_id}", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["assessment"])
async def delete_assessment_by_id(assessment_id: str):
    try:
        # Validate the ObjectId format for assessment_id
        if not ObjectId.is_valid(assessment_id):
            raise HTTPException(status_code=400, detail="Invalid assessment_id")

        # Attempt to delete the assessment document from MongoDB
        result = assessment_collection.delete_one({"_id": ObjectId(assessment_id)})

        if result.deleted_count == 1:
            return {"message": f"Assessment with ID {assessment_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Assessment with ID {assessment_id} not found")

    except HTTPException as e:
        # Reraise HTTPException if already raised
        raise e
    except Exception as e:
        # Handle any other exceptions, e.g., ObjectId conversion fails or query encounters an error
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

@assessment.post("/assessments/new/{class_id}", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["assessment"])
async def create_assessment(class_id: str, topic: str, submission_date: str, max_marks: int,exercise_data: UploadFile = File(...)):
    # Check if class exists
    assessment_doc = class_collection.find_one({"_id": ObjectId(class_id)})
    if not assessment_doc:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Save file to GridFS
    exercise_data = fs.put(exercise_data.file, filename=exercise_data.filename)
    
    # Save metadata to MongoDB
    new_assessment = {
        "class_id": class_id,
        "topic": topic,
        "max_marks": max_marks,
        "submission_date": datetime.fromisoformat(submission_date).isoformat(),
        "exercise_data": str(exercise_data),
        "upload_date": datetime.utcnow().isoformat()
    }
    
    # Insert metadata into study_exercise_datas collection
    db.assessment_collection.insert_one(new_assessment)
    
    return {"message": "Study exercise_data uploaded successfully"}


