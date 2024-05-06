from fastapi import APIRouter, Body, HTTPException, Path, UploadFile, File, Response, Depends
from models.study_materials import StudyMaterial
from config.database import db, fs
from auth.jwt_handler import signJWT
from auth.auth_bearer import jwtBearer
from bson import ObjectId
from datetime import datetime
from gridfs import GridFS
import mimetypes
from schema.studymaterial_schema import material_list

studymaterial = APIRouter()
fs = GridFS(db)

class_collection = db["class_collection"]
material_collection = db["material_collection"] 

@studymaterial.post("/upload/studymaterial/{class_id}/", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["studymaterial"]) #, dependencies=[Depends(jwtBearer())]
async def upload_study_material(class_id: str, description: str, material: UploadFile = File(...)): #, description: str = None
    # Check if class exists
    class_doc = class_collection.find_one({"_id": ObjectId(class_id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Save file to GridFS
    material = fs.put(material.file, filename=material.filename)
    
    # Save metadata to MongoDB
    study_material = {
        "class_id": class_id,
        "description": description,
        "material": str(material),
        "upload_date": datetime.utcnow()
    }
    
    # Insert metadata into study_materials collection
    db.material_collection.insert_one(study_material)
    
    return {"message": "Study material uploaded successfully"}


@studymaterial.get("/study_materials/{class_id}", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["studymaterial"]) # , dependencies=[Depends(jwtBearer())]
async def get_study_materials_by_class(class_id: str):
    try:
        # Check if class exists
        class_doc = class_collection.find_one({"_id": ObjectId(class_id)})
        if not class_doc:
            raise HTTPException(status_code=404, detail="Class not found")

        # Retrieve study materials for the given class ID
        study_materials = []
        for file_info in db.material_collection.find({"class_id": class_id}):
            description = file_info["description"]
            material = file_info["material"]
            upload_date = file_info["upload_date"]

            study_materials.append({
                "description": description,
                "upload_date": upload_date,
                "material": material
            })

        return study_materials
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail="Failed to retrieve study materials")



@studymaterial.get("/download/studymaterial/{study_material_id}", dependencies=[Depends(jwtBearer(roles = ["teacher", "student"]))], tags=["studymaterial"]) #, dependencies=[Depends(jwtBearer())]
async def download_study_material(study_material_id: str = Path(..., title="The ID of the study material")):
    try:

        # Verify if study material exists and belongs to the specified class
        study_material = db.material_collection.find_one({"_id": ObjectId(study_material_id)})
        if study_material is None:
            raise HTTPException(status_code=404, detail="Study material not found for this class")

        # Retrieve file from GridFS using the file ID stored in the study material
        file_info = fs.get(ObjectId(study_material["material"]))
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




@studymaterial.delete("/delete/studymaterial/{study_material_id}", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["studymaterial"]) # , dependencies=[Depends(jwtBearer())]
async def delete_study_material(study_material_id: str = Path(..., title="The ID of the study material")):
    try:

        # Retrieve study material from the study material collection
        study_material = db.material_collection.find_one({"_id": ObjectId(study_material_id)})
        if study_material is None:
            raise HTTPException(status_code=404, detail="Study material not found for this class")

        # Delete the file from GridFS
        fs.delete(ObjectId(study_material["material"]))

        # Delete the study material document from the collection
        db.material_collection.delete_one({"_id": ObjectId(study_material_id)})

        return {"message": "Study material deleted successfully"}
    except HTTPException:
        # Re-raise HTTPException to return specific error responses
        raise
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail="Failed to delete study material")

