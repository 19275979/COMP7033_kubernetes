'''from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status
from database import db
from models.staffs import Staff
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

auth_router = APIRouter(prefix= '/auth', tags = ['auth'])

SECRET_KEY = 'rgjr8tu49u30jier34roierjtkhtierhkejtoij9rt0945t09jbjhbjhb'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated= 'auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

class CreateUserRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

def get_db():
    database = db()
    try:
        yield database
    finally:
        database.close()

db_dependancy = Annotated [Session , Depends(get_db) ]'''