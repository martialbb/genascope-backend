from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.schemas import Token, TokenData, UserRole, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Mock user database - in a real app, this would be stored in a database
USERS_DB = {
    "admin@cancergenix.com": {
        "username": "admin@cancergenix.com",
        "full_name": "Admin User",
        "email": "admin@cancergenix.com",
        "hashed_password": "fakehashedsecret",  # In a real app, use proper password hashing
        "disabled": False,
        "user_id": "usr_admin",
        "role": UserRole.ADMIN
    }
}

# JWT Configuration
SECRET_KEY = "cancergenix_development_secret_key"  # In production, use a proper secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# We still need a user model for the auth workflow
class User:
    def __init__(self, username: str, email: Optional[str] = None, 
                 full_name: Optional[str] = None, disabled: Optional[bool] = None,
                 user_id: Optional[str] = None, role: Optional[UserRole] = None):
        self.username = username
        self.email = email
        self.full_name = full_name
        self.disabled = disabled
        self.user_id = user_id
        self.role = role

class UserInDB(User):
    def __init__(self, hashed_password: str, **kwargs):
        super().__init__(**kwargs)
        self.hashed_password = hashed_password

# Utilities
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    # In a real app, verify the password hash here
    if password != "password":  # Simplified for demo
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        role: str = payload.get("role")
        
        if email is None:
            raise credentials_exception
            
        token_data = TokenData(
            email=email,
            user_id=user_id,
            role=role,
            exp=payload.get("exp")
        )
    except JWTError:
        raise credentials_exception
        
    user = get_user(USERS_DB, username=email)  # Use email as username
    if user is None:
        raise credentials_exception
        
    # Add the role and user_id to the user object if they're not already set
    if not hasattr(user, 'user_id') or not user.user_id:
        user.user_id = token_data.user_id
    
    if not hasattr(user, 'role') or not user.role:
        user.role = token_data.role
        
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Endpoints
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(USERS_DB, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.user_id,
            "role": user.role.value if user.role else UserRole.PATIENT.value
        }, 
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": user.user_id,
        "role": user.role.value if user.role else UserRole.PATIENT.value
    }

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    # Convert User class instance to dict to match UserResponse schema
    return {
        "id": current_user.user_id,
        "email": current_user.email,
        "first_name": current_user.full_name.split()[0] if current_user.full_name else "",
        "last_name": current_user.full_name.split()[1] if current_user.full_name and len(current_user.full_name.split()) > 1 else "",
        "role": current_user.role,
        "is_active": not current_user.disabled,
        "phone": None  # Placeholder as we don't have this in our User class
    }
