def results_individual_serial(result) -> dict:
    return {
        "result_id": str(result["_id"]),
        "answer_id": result["answer_id"],
        "marks": result["marks"],
        "feedback": result["feedback"],
        "upload_date": result["upload_date"],
    }

def result_list(results) -> list:
    return [results_individual_serial(result) for result in results]



# Answers collection
def answers_individual_serial(answer) -> dict:
    return {
        "answer_id": str(answer["_id"]),
        "assessment_id": answer["assessment_id"],
        "student_id": answer["student_id"],
        "upload_date": answer["upload_date"],
        "answer_sheet": answer["answer_sheet"]
    }

def answers_list(answers) -> list:
    return [answers_individual_serial(answer) for answer in answers]
