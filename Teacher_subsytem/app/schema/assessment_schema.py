def assessment_individual_serial(assessment) -> dict:
    return {
        "assessment_id": str(assessment["_id"]),
        "class_id": assessment["class_id"],
        "topic": assessment["topic"],
        "exercise_data": assessment["exercise_data"],
        "upload_date": assessment["upload_date"],
        "submission_date": assessment["submission_date"],
        "max_marks": assessment["max_marks"],   
    }

def assessment_list(assessments) -> list:
    return [assessment_individual_serial(assessment) for assessment in assessments]

