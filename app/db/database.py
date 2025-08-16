from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Create engine with URL from settings (handles both local and production)
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=300,    # Recycle connections every 5 minutes
    echo=False          # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for ORM models
Base = declarative_base()

# Models are imported in app/models/__init__.py to register them with Base
# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
