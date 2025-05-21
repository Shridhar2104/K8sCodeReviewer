import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.router import router as api_router
from app.config import settings

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Code Review LLM Service",
    description="AI-powered code review service using LLMs",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(
    api_router,
    prefix=settings.API_PREFIX,
    tags=["review"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Code Review LLM Service API",
        "docs_url": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)