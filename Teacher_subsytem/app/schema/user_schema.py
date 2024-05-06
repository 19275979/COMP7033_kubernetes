def individual_serial(user) -> dict:
    return {
            "user_id" : str(user["_id"]),
            "name" : user["name"],
            "email" : user["email"],
        }
        

def user_list(users) -> list:
    return [individual_serial(user) for user in users]