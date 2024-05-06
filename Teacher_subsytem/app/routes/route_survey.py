from fastapi import APIRouter, Body, HTTPException, Path , UploadFile, File, HTTPException
from models.surveys import  Survey, SurveyResponse
from schema.survey_schema import survey_list, survey_individual_serial, survey_response_individual_serial, survey_response_list
from config.database import db
from auth.jwt_handler import signJWT
from auth.auth_bearer import jwtBearer
from bson import ObjectId
from datetime import datetime

survey = APIRouter()


staff_collection = db ["staff_collection"]
survey_collection = db["survey_collection"]
survey_response_collection = db["survey_response_collection"]

# GET surveys by staff id 
@survey.get("/survey/staff/{staff_id}", tags=["survey"])
async def get_surveys_by_staff(staff_id: str):
    try:
        # Find surveys where staff_id is in the list of staff_ids
        surveys = survey_list(survey_collection.find({"staff_id": staff_id}))

        if surveys:
            return surveys
        else:
            raise HTTPException(status_code=404, detail=f"No surveys found for staff ID: {staff_id}")

    except Exception as e:
        # Handle any exceptions, e.g., if ObjectId conversion fails or query encounters an error
        raise HTTPException(status_code=500, detail="Internal Server Error")

@survey.post("/surveys/new", tags=["survey"])
async def create_survey(survey: Survey):
    try:
        # Create a new survey document
        new_survey = {
            "staff_id": survey.staff_id,
            "description": survey.description,
            "survey_form": survey.survey_form,
            "upload_date": survey.upload_date,
            "submission_date": survey.submission_date
        }

        # Insert the new survey document into the database
        result = survey_collection.insert_one(new_survey)

        # If insertion was successful, return the created survey
        if result.inserted_id:
            survey_created = survey.dict()
            survey_created["id"] = str(result.inserted_id)
            return survey_created
        else:
            raise HTTPException(status_code=500, detail="Failed to create survey")

    except Exception as e:
        # Handle any exceptions, e.g., validation errors or database errors
        raise HTTPException(status_code=500, detail=str(e))
    
# POST Survey response 
@survey.post("/surveys/response", tags=["survey response"])
async def create_survey_response(survey_response: SurveyResponse):
    try:
        # Retrieve the corresponding survey document
        survey = survey_collection.find_one({"_id": ObjectId(survey_response.survey_id)})
        if not survey:
            raise HTTPException(status_code=404, detail=f"Survey with ID {survey_response.survey_id} not found")

        # Check if the provided staff_id is in the staff_ids list of the survey
        if survey_response.staff_id not in survey["staff_id"]:
            raise HTTPException(status_code=400, detail=f"Staff ID {survey_response.staff_id} is not valid for the specified survey")

        # Create a new survey response document
        new_survey_response = {
            "survey_id": survey_response.survey_id,
            "staff_id": survey_response.staff_id,
            "response": survey_response.response,
            "upload_date": survey_response.upload_date
        }

        # Insert the new survey response document into the database
        result = survey_response_collection.insert_one(new_survey_response)

        # If insertion was successful, return the created survey response
        if result.inserted_id:
            survey_response_created = survey_response.dict()
            survey_response_created["id"] = str(result.inserted_id)
            return survey_response_created
        else:
            raise HTTPException(status_code=500, detail="Failed to create survey response")

    except Exception as e:
        # Handle any exceptions, e.g., validation errors or database errors
        raise HTTPException(status_code=500, detail=str(e))
    
@survey.get("/surveyresponse/staff/{staff_id}", tags=["survey response"])
async def get_survey_response_by_staff(staff_id: str):
    # Find survey_response based on the provided staff_id
    survey_response = survey_response_list(survey_response_collection.find({"staff_id": staff_id}))

    if survey_response:
        return survey_response
    else:
        raise HTTPException(status_code=404, detail=f"No survey_response found for class ID: {staff_id}")

    
@survey.get("/survey/response/{survey_id}", tags=["survey response"])
async def get_survey_responses_by_survey(survey_id: str):
    try:
        # Find survey responses based on the provided survey_id
        survey_responses = survey_response_collection.find({"survey_id": survey_id})

        # Serialize survey responses into the desired format
        serialized_survey_responses = survey_response_list(survey_responses) 

        return serialized_survey_responses

    except Exception as e:
        # Handle any exceptions, e.g., if ObjectId conversion fails or query encounters an error
        raise HTTPException(status_code=500, detail="Internal Server Error")