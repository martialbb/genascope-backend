#!/usr/bin/env python3
"""
Script to create or update a user with genascope/genascope credentials
"""
import sys
import os
from passlib.context import CryptContext

# Add the app directory to the Python path
sys.path.append('/app')

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Generate a password hash"""
    return pwd_context.hash(password)

if __name__ == "__main__":
    # Generate hash for 'genascope' password
    password_hash = hash_password("genascope")
    print(f"Password hash for 'genascope': {password_hash}")
