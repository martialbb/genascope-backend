import sys
from datetime import datetime, timedelta, timezone
from jose import jwt

# Constants from app.api.auth - defined here for a standalone script
SECRET_KEY = "genascope_development_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

def generate_token(email: str, role: str, user_id: str):
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    now = datetime.now(timezone.utc)
    expires_at = now + expires_delta
    
    payload = {
        "sub": email,       # Expected by get_current_user for email
        "id": user_id,      # Expected by get_current_user for user_id
        "role": role,       # Used for role checks
        "exp": expires_at,  # Standard JWT expiry claim
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    print(token)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python generate_jwt_token.py <email> <role> <user_id>")
        print("Example: python generate_jwt_token.py admin@testhospital.com admin admin-001")
        sys.exit(1)
    
    email_arg = sys.argv[1]
    role_arg = sys.argv[2]
    user_id_arg = sys.argv[3]
    generate_token(email_arg, role_arg, user_id_arg)
