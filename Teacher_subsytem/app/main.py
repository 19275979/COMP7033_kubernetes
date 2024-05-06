from fastapi import FastAPI, Body, Depends
from routes.route_user import user
from routes.route_student import student
from routes.route_class import classroom
from routes.route_assessment import assessment
from routes.route_study_material import studymaterial
from routes.route_survey import survey
from routes.route_student_marks import student_marks

app = FastAPI()

app.include_router(user)
app.include_router(student)
app.include_router(classroom)
app.include_router(studymaterial)
app.include_router(assessment)
app.include_router(survey)
app.include_router(student_marks)



