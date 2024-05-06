from fastapi import APIRouter, Body, HTTPException, Path , UploadFile, File, HTTPException, Response, Depends
from models.student_marks import  Results, Answers
from schema.student_marks_schema import result_list, results_individual_serial, answers_individual_serial, answers_list
from config.database import db
from auth.jwt_handler import signJWT
from auth.auth_bearer import jwtBearer
from bson import ObjectId
from datetime import datetime
from gridfs import GridFS
import mimetypes

student_marks = APIRouter()
fs = GridFS(db)

results_collection = db["results_collection"]
answers_collection = db["answers_collection"]
assessment_collection = db["assessment_collection"]

# GET endpoint to query from assessment id and student id 
@student_marks.get("/answers/download/assessment/{assessment_id}/student/{student_id}", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["answers"])
async def download_answers_by_student(student_id: str, assessment_id: str ):
    try:
        # Find answers based on the provided assessment_id
        answer = answers_collection.find_one({"student_id": student_id, "assessment_id": assessment_id})
        if answer is None:
            raise HTTPException(status_code=404, detail="Answer not found for this class")

        # Retrieve file from GridFS using the file ID stored in the study material
        file_info = fs.get(ObjectId(answer["answer_sheet"]))
        if file_info is None:
            raise HTTPException(status_code=404, detail="File not found")

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
        raise HTTPException(status_code=500, detail="Failed to download study material")


@student_marks.get("/answers/assessment_id/{assessment_id}", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["answers"])
async def get_answers_by_assessment(assessment_id: str):
    try:
        # Find answers based on the provided assessment_id
        answers = answers_collection.find({"assessment_id": assessment_id})

        # Serialize answers into a list of dictionaries
        serialized_answers = answers_list(answers)

        return serialized_answers

    except Exception as e:
        # Handle any exceptions, e.g., if ObjectId conversion fails or query encounters an error
        raise HTTPException(status_code=500, detail="Internal Server Error")
    


@student_marks.get("/answers/view/assessment_id/{assessment_id}/student/{student_id}", dependencies=[Depends(jwtBearer(roles = ["teacher", "student"]))], tags=["answers"])
async def view_answers_by_student(student_id: str, assessment_id: str):
    try:
        # Find all answers
        answer = answers_collection.find_one({"student_id": student_id, "assessment_id": assessment_id})
        if answer is None:
            raise HTTPException(status_code=404, detail="Answer not found for this class")

        serialized_answer = {
            "answer_id": str(answer["_id"]),
            "assessment_id": answer["assessment_id"],
            "student_id": answer["student_id"],
            "upload_date": answer["upload_date"],
            "answer_sheet": answer["answer_sheet"]
        }

        return serialized_answer

    except Exception as e:
        # Handle any exceptions, e.g., if query encounters an error
        raise HTTPException(status_code=500, detail="Internal Server Error")


###### RESULTS ####### 

@student_marks.get("/results/by_assessment_id/{assessment_id}/", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["results"])
async def get_results_by_id(assessment_id: str):
    try:
        # Find the answer documents based on the provided assessment_id
        answer_documents = answers_collection.find({"assessment_id": assessment_id})

        # Initialize a list to store result documents
        result_documents = []

        # Loop through each answer document
        for answer_document in answer_documents:
            # Get the answer_id from the current answer document
            answer_id = answer_document["_id"]
            student_id = answer_document["student_id"]  # Get student_id from answer_document

            # Find the result document based on the answer_id
            result_document = results_collection.find_one({"answer_id": str(answer_id)})

            # If result document exists, append it to the result_documents list
            if result_document:
                # Serialize the result_document
                result_serialized = results_individual_serial(result_document)

                # Add student_id to the serialized result_document
                result_serialized["student_id"] = student_id

                result_documents.append(result_serialized)
        
        # Check if any result documents were found
        if result_documents:
            return result_documents
        else:
            raise HTTPException(status_code=404, detail="Results not found for the provided assessment")

    except Exception as e:
        # Handle any exceptions
        raise HTTPException(status_code=500, detail="Internal Server Error")



@student_marks.put("/results/update/assessment_id/{assessment_id}/student/{student_id}/", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["results"])
async def update_results_by_id(assessment_id: str, student_id: str, marks: float, feedback: str):
    try:
        # Find the answer document based on the provided assessment_id and student_id
        answer_document = answers_collection.find_one({"assessment_id": assessment_id, "student_id": student_id})

        # Check if the answer document exists
        if answer_document:
            # Get the answer_id from the answer document
            answer_id = answer_document["_id"]

            # Find the result document based on the answer_id
            result_document = results_collection.find_one({"answer_id": str(answer_id)})

            # Check if the result document exists
            if result_document:
                # Update the result document with the provided data
                results_collection.update_one(
                    {"_id": result_document["_id"]},
                    {"$set": {
                        "marks": marks,
                        "feedback": feedback,
                        "upload_date": datetime.utcnow()
                    }}
                )

                return {"message": "Results updated successfully"}
            else:
                raise HTTPException(status_code=404, detail="Results not found for the provided assessment and student")
        else:
            raise HTTPException(status_code=404, detail=f"No answer document found for assessment_id: {assessment_id} and student_id: {student_id}")

    except Exception as e:
        # Handle any exceptions
        raise HTTPException(status_code=500, detail="Internal Server Error")


@student_marks.post("/results/upload/{answer_id}", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["results"])
async def post_results(answer_id: str, marks: str, feedback: str):
    try:
        # Check if the answer_id exists in the answers_collection
        answer = answers_collection.find_one({"_id": ObjectId(answer_id)})
        if not answer:
            raise HTTPException(status_code=404, detail=f"Answer with ID {answer_id} not found")

        # Create a new results document
        new_results = {
            "answer_id": answer_id,
            "marks": marks,
            "feedback": feedback,
            "upload_date": datetime.utcnow()
        }

        # Insert the new results document into the database
        result = results_collection.insert_one(new_results)

        # If insertion was successful, return the created results
        if result.inserted_id:
            results_created = new_results
            results_created["id"] = str(result.inserted_id)
            return results_created
        else:
            raise HTTPException(status_code=500, detail="Failed to post results")

    except Exception as e:
        # Handle any exceptions, e.g., validation errors or database errors
        raise HTTPException(status_code=500, detail=str(e))

##########  STUB AND TESTING APIs ##########












'''




    
@student_marks.get("/results/{result_id}", dependencies=[Depends(jwtBearer(roles = ["teacher", "student"]))], tags=["results"])
async def get_results_by_id(result_id: str):
    try:
        # Find the results document based on the provided result_id
        result = results_collection.find_one({"_id": ObjectId(result_id)})

        # Check if the result exists
        if result:
            return result
        else:
            raise HTTPException(status_code=404, detail=f"Results with ID {result_id} not found")

    except Exception as e:
        # Handle any exceptions, e.g., ObjectId conversion error or database query error
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

@student_marks.get("/results/assessment_id/{assessment_id}/student/{student_id}/", dependencies=[Depends(jwtBearer(roles = ["teacher", "student"]))], tags=["results"])
async def get_results_by_id(assessment_id: str, student_id: str ):
    try:
        # Find the results document based on the provided result_id
        answer_document = answers_collection.find_one({"assessment_id": assessment_id, "student_id": student_id})

        # Check if the result exists
        if answer_document:
            answer_id = answer_document["_id"]
        else:
            raise HTTPException(status_code=404, detail=f"Results with ID not found")

        result_document = results_collection.find_one({"answer_id": str(answer_id)})

        # Check if the result document exists
        if result_document:
            return result_document
        else:
            raise HTTPException(status_code=404, detail="Results not found for the provided assessment and student")


    except Exception as e:
        # Handle any exceptions, e.g., ObjectId conversion error or database query error
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
from fastapi import HTTPException

@student_marks.put("/results/update/assessment_id/{assessment_id}/student/{student_id}/", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["results"])
async def update_results_by_id(assessment_id: str, student_id: str, marks: float, feedback: str):
    try:
        # Find the answer document based on the provided assessment_id and student_id
        answer_document = answers_collection.find_one({"assessment_id": assessment_id, "student_id": student_id})

        # Check if the answer document exists
        if answer_document:
            # Get the answer_id from the answer document
            answer_id = answer_document["_id"]

            # Find the result document based on the answer_id
            result_document = results_collection.find_one({"answer_id": str(answer_id)})

            # Check if the result document exists
            if result_document:
                # Update the result document with the provided data
                results_collection.update_one(
                    {"_id": result_document["_id"]},
                    {"$set": {
                        "marks": marks,
                        "feedback": feedback,
                        "upload_date": datetime.utcnow()
                    }}
                )

                return {"message": "Results updated successfully"}
            else:
                raise HTTPException(status_code=404, detail="Results not found for the provided assessment and student")
        else:
            raise HTTPException(status_code=404, detail=f"No answer document found for assessment_id: {assessment_id} and student_id: {student_id}")

    except Exception as e:
        # Handle any exceptions
        raise HTTPException(status_code=500, detail="Internal Server Error")






@student_marks.put("/results/update/{result_id}", tags=["results"], dependencies=[Depends(jwtBearer(roles = ["teacher"]))])
async def update_assessment_by_id(result_id: str , answer_id: str , feedback: str , new_marks: float):
    try:
        # Retrieve assessment from the assessment collection
        assessment_doc = results_collection.find_one({"_id": ObjectId(result_id)})
        if not assessment_doc:
            raise HTTPException(status_code=404, detail="Assessment not found")

        # Update the assessment document with the new file ID, topic, and max_marks
        results_collection.update_one(
            {"_id": ObjectId(result_id)},
            {"$set": {
                "feedback": feedback,
                "answer_id": answer_id,
                "marks": new_marks,
                "upload_date": datetime.utcnow()
            }}
        )

        return{"answer_id": answer_id, "marks": new_marks, "feedback": feedback, "upload_date": datetime.utcnow()} 
  

    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail="Failed to update assessment file, topic, and max_marks")
'''

####### NOT NEEDED FOR DEPLOYMENT #######


@student_marks.post("/answers/new/{assessment_id}", dependencies=[Depends(jwtBearer(roles = ["teacher", "student"]))], tags=["answers"]) #NOT TEACHER BUT FOR TESTING
async def post_answers(assessment_id: str, student_id: str, answer_sheet: UploadFile = File(...) ):
    try:
        # Check if the assessment_id exists in the assessment_collection
        assessment = assessment_collection.find_one({"_id": ObjectId(assessment_id)})
        if not assessment:
            raise HTTPException(status_code=404, detail=f"Assessment with ID {assessment_id} not found")

        # Save file to GridFS
        answer_sheet = fs.put(answer_sheet.file, filename=answer_sheet.filename)
    
        # Create a new answers document
        new_answers = {
            "assessment_id": assessment_id,
            "student_id": student_id,
            "upload_date": datetime.utcnow(),
            "answer_sheet": str(answer_sheet)
        }

        # Insert the new answers document into the database
        result = answers_collection.insert_one(new_answers)

        # If insertion was successful, return the created answers
        if result.inserted_id:
            return {"message": "answers uploaded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to post answers")

    except Exception as e:
        # Handle any exceptions, e.g., validation errors or database errors
        raise HTTPException(status_code=500, detail=str(e))
    




