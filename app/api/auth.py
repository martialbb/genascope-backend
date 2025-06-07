from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.users import UserService
from app.schemas.users import UserRole, UserCreate, UserResponse, UserInDB
from app.schemas.common import Token, TokenData

router = APIRouter(prefix="/api/auth", tags=["auth"])

# JWT Configuration
SECRET_KEY = "genascope_development_secret_key"  # In production, use a proper secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# OAuth2 password bearer token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# We still need a user model for the auth workflow
class User:
    def __init__(self, username: str, email: Optional[str] = None, 
                 full_name: Optional[str] = None, disabled: Optional[bool] = None,
                 user_id: Optional[str] = None, role: Optional[str] = None,
                 account_id: Optional[str] = None):
        self.username = username
        self.email = email or username
        self.full_name = full_name
        self.disabled = disabled
        self.id = user_id
        self.role = role  # Make sure role is properly initialized
        self.account_id = account_id  # Add account_id attribute

    def __str__(self):
        return f"User(id={self.id}, username={self.username}, role={self.role}, account_id={self.account_id})"

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Enhanced get_current_user function
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get the current authenticated user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")  # Use 'sub' for email
        user_id: str = payload.get("id")
        
        if email is None or user_id is None:
            raise credentials_exception
            
        token_data = TokenData(email=email, user_id=user_id)

        # Get user from database
        user_service = UserService(db)
        db_user = user_service.get_user_by_email(token_data.email)

        if db_user is None:
            raise credentials_exception

        return User(
            username=db_user.email,
            email=db_user.email,
            full_name=db_user.name,
            disabled=not db_user.is_active,
            user_id=db_user.id,
            role=db_user.role,
            account_id=db_user.account_id
        )

    except JWTError as e:
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint to get access token"""
    user_service = UserService(db)
    user = user_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "id": str(user.id), "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    user_service = UserService(db)
    try:
        user = user_service.create_user(user_data.model_dump())
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get the current user's information"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.full_name,
        "role": current_user.role,
        "is_active": not current_user.disabled,
        "account_id": str(current_user.account_id) if current_user.account_id else None,
        "clinician_id": None  # Will be implemented when needed
    }

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user - wrapper function for tests"""
    user_service = UserService(db)
    db_user = user_service.authenticate_user(username, password)
    
    if not db_user:
        return None
        
    return User(
        username=db_user.email,
        email=db_user.email,
        full_name=db_user.name,
        disabled=not db_user.is_active,
        user_id=db_user.id,
        role=db_user.role.value
    )

