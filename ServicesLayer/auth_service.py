USERS = {
    "admin": {"role": "admin"},
    "doctor": {"role": "doctor"},
    "analyst": {"role": "analyst"}
}


def get_user_role(username: str):
    user = USERS.get(username)
    if not user:
        return None
    return user["role"]