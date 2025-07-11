from fastapi import FastAPI
from app.config.settings import settings
from app.api.routes import api_router

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION
)

# Include API routes
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG
    ) 