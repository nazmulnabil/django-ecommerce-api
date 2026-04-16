from .models import User

def get_user_profile_domain(user: User) -> dict:
  
    return {
        "user_id": user.id,
        "email_address": user.email, # Note: We can rename fields here
        "full_username": user.username,
        "bio": user.bio,
    }


def register_user(data: dict) -> User:
    # Use create_user (this handles password hashing for you!)
    user = User.objects.create_user(
        email=data['email'],
        username=data['username'],
        password=data['password'],
        bio=data.get('bio', '')
    )
    return user