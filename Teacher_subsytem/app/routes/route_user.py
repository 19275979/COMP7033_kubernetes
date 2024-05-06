from fastapi import APIRouter, Body, HTTPException, Path, Depends
from models.user import User, UserLogin
from schema.user_schema import user_list
from config.database import db
from auth.jwt_handler import signJWT
from auth.auth_bearer import jwtBearer
from pydantic import EmailStr
import bcrypt

user = APIRouter()

user_collection = db ["user_collection"]


# User Login
@user.post("/user/login", tags=["user"])
async def user_login(user_login: UserLogin = Body(default=None)):
    # Search for user in MongoDB collection
    user = user_collection.find_one({"email": user_login.email})
    if user and bcrypt.checkpw(user_login.password.encode('utf-8'), user['password'].encode('utf-8')):
        return signJWT(user_login.email, "teacher")
    else:
        raise HTTPException(status_code=401, detail="Invalid login details")



                    ########## STUB AND TESTING APIs ##########



# User Signup [Create a new user] 
@user.post("/user/signup", tags=["user"])
async def user_signup(user: User = Body(default=None)):
    # Check if email already exists in the database
    existing_user = user_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    # Insert user into MongoDB collection
    user_collection.insert_one({
        "name": user.name,
        "email": user.email,
        "password": hashed_password.decode('utf-8'),
    })
    return signJWT(user.email, "teacher")

# Get all user from the database
@user.get("/user", dependencies=[Depends(jwtBearer(roles = ["teacher"]))], tags=["user"])
async def get_users():
    users = user_list(user_collection.find())
    return users


