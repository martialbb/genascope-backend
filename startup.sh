#!/bin/bash
set -e

echo "🏗️ Starting application setup..."

# Display environment info
echo "📋 Environment variables:"
echo "DATABASE_URL: ${DATABASE_URL}"

echo "⏳ Skipping database connectivity check and proceeding with setup..."

# Set up database tables
echo "🏗️ Setting up database tables..."
python << EOF
import sys
import os
sys.path.append('/app')

# Check if we should skip automatic database setup
if os.environ.get('SKIP_AUTO_SETUP') == 'true':
    print("ℹ️ Skipping automatic database setup (SKIP_AUTO_SETUP=true)")
    print("📋 This is typically used during database restoration")
    exit(0)

try:
    from app.db.database import engine, Base
    # Import all models to ensure all tables are created
    from app.models import *  # This imports all models from __init__.py
    from app.models.user import User
    from app.models.accounts import Account
    
    print("Creating database tables...")
    # Create tables with IF NOT EXISTS handling
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("✅ Database tables created successfully")
    except Exception as table_error:
        print(f"⚠️ Table creation warning (may already exist): {table_error}")
        # Continue anyway
    
    # Create test user if not exists
    from sqlalchemy.orm import sessionmaker
    from app.core.security import get_password_hash
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check if admin user exists
    admin_user = session.query(User).filter(User.email == 'admin@test.com').first()
    if not admin_user:
        print("Creating test admin user...")
        # Create account first
        account = Account(name="Test Account")
        session.add(account)
        session.flush()  # Get the account ID
        
        # Create user
        hashed_password = get_password_hash("test123")
        user = User(
            id="admin-user-001",
            email="admin@test.com",
            hashed_password=hashed_password,
            name="Admin User",
            role="admin",
            is_active=True,
            account_id=account.id
        )
        session.add(user)
        session.commit()
        print("✅ Test admin user created")
    else:
        print("✅ Admin user already exists")
    
    session.close()
    print("✅ Database setup completed")
    
except Exception as e:
    print(f"❌ Database setup failed: {e}")
    import traceback
    traceback.print_exc()
    # Continue anyway - the app might still work
    
EOF

echo "🚀 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 1
