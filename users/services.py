from .models import User

def get_user_profile_domain(user: User) -> dict:
  
    return {
        "user_id": user.id,
        "email_address": user.email, # Note: We can rename fields here
        "full_username": user.username,
        "bio": user.bio,
    }