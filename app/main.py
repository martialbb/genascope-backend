from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router

app = FastAPI(
    title="Genascope API",
    description="""
    Backend API for Genascope cancer screening platform.
    
    ## Features
    
    * **Chat Assessment**: Conduct interactive patient assessments
    * **Accounts Management**: Create, list, update and delete organization accounts
    * **User Management**: Comprehensive CRUD operations for users with role-based access
    * **Eligibility Analysis**: Process assessment results to determine screening eligibility
    * **Appointments**: Schedule and manage appointments
    * **Laboratory Integration**: Order and track test results
    
    ## Authentication
    
    Most endpoints require authentication using JWT Bearer tokens.
    Login via POST /api/auth/token to receive an access token.
    """,
    version="0.2.0",
    contact={
        "name": "Genascope Support",
        "email": "support@genascope.example.com",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://genascope.example.com/license",
    },
    swagger_ui_parameters={"defaultModelsExpandDepth": 1},
)

# Configure CORS - update with your frontend URL when deployed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4321"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

@app.get("/health", tags=["system"])
async def health_check():
    """
    Simple health check endpoint to verify API is running.
    Returns status 'ok' when the service is operational.
    """
    return {"status": "ok"}
