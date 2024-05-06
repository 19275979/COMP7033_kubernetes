def survey_individual_serial(survey) -> dict:
    return {
            "survey_id" : str(survey["_id"]),
            "staff_id" : [str(staff_id) for staff_id in survey["staff_id"]],
            "description" : survey["description"],
            "survey_form" : survey["survey_form"],
            "upload_date" : survey["upload_date"],
            "submission_date" : survey["submission_date"]
        }

def survey_list(surveys) -> list:
    return [survey_individual_serial(survey) for survey in surveys]



# Schema for Survey Responses

def survey_response_individual_serial(survey_response) -> dict:
    return {
            "survey_response_id" : str(survey_response["_id"]),
            "survey_id" : survey_response["survey_id"],
            "staff_id" : survey_response["staff_id"],
            "response" : survey_response["response"],
            "upload_date" : survey_response["upload_date"],
        }

def survey_response_list(survey_responses) -> list:
    return [survey_response_individual_serial(survey_response) for survey_response in survey_responses]

