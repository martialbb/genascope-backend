from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router

app = FastAPI(
    title="Genascope API",
    description="Backend API for Genascope chat application",
    version="0.1.0",
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

@app.get("/health")
async def health_check():
    return {"status": "ok"}
