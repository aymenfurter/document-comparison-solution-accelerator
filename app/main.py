from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.routers import compare
from app.core.config import settings
import os

app = FastAPI(
    title="Document Comparison API",
    description="API for comparing Word documents and generating intelligent changelogs",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static files directory (if it exists)
if os.path.exists("/app/static/assets"):
    app.mount("/assets", StaticFiles(directory="/app/static/assets"), name="static")


@app.get("/")
async def read_root():
    return FileResponse("/app/static/index.html")

# Include routers
app.include_router(compare.router, prefix="/api/v1", tags=["comparison"])

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
