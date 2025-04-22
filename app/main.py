from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
import torch
from app.api.routes import router as api_router
from app.core.session_manager import SessionManager
# from app.utils.cache_utils import init_cache
from app.utils.logging_config import logger

# Initialize FastAPI application
logger.info("Initializing FastAPI application...")
app = FastAPI(title="Twitter Support Chatbot")

# Setup CORS middleware
logger.info("Setting up CORS middleware...")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins (adjust in production for security)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
logger.info("Mounting static files directory...")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
logger.info("Setting up Jinja2 templates...")
templates = Jinja2Templates(directory="app/templates")

# Initialize session manager with GCS configuration
logger.info("Initializing session manager...")
gcs_bucket = os.getenv("GCS_BUCKET_NAME")
gcs_credentials = os.getenv("GCS_CREDENTIALS_PATH")
session_manager = SessionManager(
    csv_file="chat_history.csv",
    gcs_bucket=gcs_bucket,
    gcs_credentials=gcs_credentials
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check that doesn't depend on external services"""
    logger.info("Health check endpoint called")
    return {"status": "healthy", "message": "API is running"}

# Include API router
logger.info("Including API router...")
app.include_router(api_router, prefix="/api")

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Render the chat UI home page"""
    logger.info("Home page requested, generating new session ID...")
    session_id = str(uuid.uuid4())
    logger.info(f"Generated session ID: {session_id}")
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "session_id": session_id}
    )

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting application services...")
    
    # Print environment variables for debugging (masking sensitive ones)
    logger.info(f"REDIS_HOST: {os.getenv('REDIS_HOST', 'not set')}")
    logger.info(f"REDIS_PORT: {os.getenv('REDIS_PORT', 'not set')}")
    logger.info(f"GCS_BUCKET_NAME: {os.getenv('GCS_BUCKET_NAME', 'not set')}")
    
    # Initialize cache with retry logic
    # logger.info("Initializing cache...")
    # cache_initialized = init_cache(app)
    # if cache_initialized:
    #     logger.info("Cache initialized successfully")
    # else:
    #     logger.warning("Cache initialization failed, continuing without cache")

# Removed the __main__ block as run.py handles server start 