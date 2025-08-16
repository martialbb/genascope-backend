from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import os

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    environment: str
    database_connected: bool = False
    services: dict = {}

@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring and deployment verification
    """
    try:
        # Basic health info
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "version": "1.0.0",  # Consider reading from version file
            "environment": os.getenv("ENVIRONMENT", "development"),
            "services": {}
        }
        
        # Check database connection
        try:
            from app.db.database import engine
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            health_data["database_connected"] = True
            health_data["services"]["database"] = "connected"
        except Exception as e:
            health_data["database_connected"] = False
            health_data["services"]["database"] = f"error: {str(e)[:100]}"
            health_data["status"] = "degraded"
        
        # Check Redis connection (if configured)
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis
                r = redis.from_url(redis_url)
                r.ping()
                health_data["services"]["redis"] = "connected"
            except Exception as e:
                health_data["services"]["redis"] = f"error: {str(e)[:100]}"
                health_data["status"] = "degraded"
        
        # Check external services
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "sk-your-openai-api-key-here":
            health_data["services"]["openai"] = "configured"
        else:
            health_data["services"]["openai"] = "not configured"
        
        if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_ACCESS_KEY_ID") != "YOUR_AWS_ACCESS_KEY_ID":
            health_data["services"]["aws"] = "configured"
        else:
            health_data["services"]["aws"] = "not configured"
            
        return HealthResponse(**health_data)
        
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            environment=os.getenv("ENVIRONMENT", "development"),
            database_connected=False,
            services={"error": str(e)[:200]}
        )

@router.get("/ready", tags=["health"])
async def readiness_check():
    """
    Kubernetes/Docker readiness probe endpoint
    """
    try:
        # Check if essential services are ready
        from app.db.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not ready", "error": str(e)}, 503

@router.get("/live", tags=["health"])
async def liveness_check():
    """
    Kubernetes/Docker liveness probe endpoint
    """
    return {"status": "alive", "timestamp": datetime.utcnow()}
