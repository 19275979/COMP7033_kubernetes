from pymongo import MongoClient
from pymongo.server_api import ServerApi
from gridfs import GridFS

client = MongoClient("mongodb+srv://19275979:KxvRg.6Np2nxru-@comp7033.tn5xzyp.mongodb.net/?retryWrites=true&w=majority&appName=COMP7033")

db = client.teacher_db # To  make database 
fs = GridFS(db) # to store file in db
