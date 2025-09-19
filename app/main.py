from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.models import AnalysisRequest, InteractionAnalysis
from app.utils import InstagramAnalyzer
from app.config import Config
import uvicorn
import logging
import asyncio
import uuid
from typing import Dict
import time

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Instagram Interaction Analyzer",
    version="2.0.0",
    description="API to analyze Instagram user interactions with robust error handling"
)

# In-memory storage for analysis results (use Redis in production)
analysis_results: Dict[str, Dict] = {}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Instagram Interaction Analyzer API", 
        "version": "2.0.0",
        "status": "active",
        "endpoints": {
            "health": "/health",
            "analyze_get": "/analyze/{user1}/{user2}",
            "analyze_post": "/analyze",
            "check_status": "/status/{task_id}"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "instagram-analyzer"}

def run_analysis(task_id: str, user1: str, user2: str, use_credentials: bool, max_posts: int, max_stories: int):
    """Background task to run analysis"""
    try:
        analyzer = InstagramAnalyzer(use_credentials=use_credentials)
        
        result = analyzer.analyze_interactions(
            user1=user1,
            user2=user2,
            max_posts=max_posts,
            max_stories=max_stories
        )
        
        analysis_results[task_id] = {
            "status": "completed",
            "result": result,
            "completed_at": time.time()
        }
        
    except Exception as e:
        analysis_results[task_id] = {
            "status": "error",
            "error": str(e),
            "completed_at": time.time()
        }

@app.post("/analyze")
async def analyze_interactions(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze interactions between two Instagram users
    - Returns a task ID immediately, check status with /status/{task_id}
    """
    try:
        # Validate input
        if not request.user1 or not request.user2:
            raise HTTPException(status_code=400, detail="Both usernames are required")
        
        if request.max_posts > 100 or request.max_posts < 1:
            request.max_posts = 30
        if request.max_stories > 50 or request.max_stories < 1:
            request.max_stories = 10
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Store initial task status
        analysis_results[task_id] = {
            "status": "processing",
            "started_at": time.time(),
            "user1": request.user1,
            "user2": request.user2
        }
        
        # Run analysis in background
        background_tasks.add_task(
            run_analysis,
            task_id,
            request.user1,
            request.user2,
            request.use_credentials,
            request.max_posts,
            request.max_stories
        )
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Analysis started in background",
            "check_status": f"http://localhost:8000/status/{task_id}"
        }
        
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/status/{task_id}")
async def check_analysis_status(task_id: str):
    """Check the status of an analysis task"""
    if task_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Task not found")
    
    result = analysis_results[task_id]
    
    if result["status"] == "completed":
        return {
            "task_id": task_id,
            "status": "completed",
            "result": result["result"]
        }
    elif result["status"] == "error":
        return {
            "task_id": task_id,
            "status": "error",
            "error": result["error"]
        }
    else:
        return {
            "task_id": task_id,
            "status": "processing",
            "started_at": result["started_at"],
            "elapsed_seconds": time.time() - result["started_at"]
        }

@app.get("/analyze/{user1}/{user2}")
async def analyze_interactions_get(user1: str, user2: str, use_credentials: bool = False):
    """
    Quick analysis via GET request (limited to basic info)
    """
    try:
        if not user1 or not user2:
            raise HTTPException(status_code=400, detail="Both usernames are required")
        
        analyzer = InstagramAnalyzer(use_credentials=use_credentials)
        
        # Get basic profile info only for quick response
        user1_profile = analyzer.get_profile(user1)
        user2_profile = analyzer.get_profile(user2)
        
        result = {
            "user1": user1,
            "user2": user2,
            "user1_followers": getattr(user1_profile, 'followers', 'Unknown'),
            "user2_followers": getattr(user2_profile, 'followers', 'Unknown'),
            "user2_following": getattr(user2_profile, 'following', 'Unknown'),
            "is_private": getattr(user2_profile, 'is_private', 'Unknown'),
            "status": "basic_info_only",
            "message": "Use POST /analyze for detailed interaction analysis"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in quick analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True,
        log_level="info"
    )


# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from app.models import AnalysisRequest, InteractionAnalysis
# from app.utils import InstagramAnalyzer
# from app.config import Config
# import uvicorn
# import logging

# logger = logging.getLogger(__name__)

# app = FastAPI(
#     title="Instagram Interaction Analyzer",
#     version="2.0.0",
#     description="API to analyze Instagram user interactions with robust error handling"
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/")
# async def root():
#     return {
#         "message": "Instagram Interaction Analyzer API", 
#         "version": "2.0.0",
#         "status": "active",
#         "endpoints": {
#             "health": "/health",
#             "analyze_get": "/analyze/{user1}/{user2}",
#             "analyze_post": "/analyze"
#         }
#     }

# @app.get("/health")
# async def health_check():
#     return {"status": "healthy", "service": "instagram-analyzer"}

# @app.post("/analyze", response_model=InteractionAnalysis)
# async def analyze_interactions(request: AnalysisRequest):
#     """
#     Analyze interactions between two Instagram users
#     - user1: The user whose interactions to analyze
#     - user2: The target user whose content to check
#     - use_credentials: Whether to use Instagram login (for private accounts)
#     - max_posts: Maximum number of posts to analyze (1-100)
#     - max_stories: Maximum number of stories to analyze (1-50)
#     """
#     try:
#         # Validate input
#         if not request.user1 or not request.user2:
#             raise HTTPException(status_code=400, detail="Both usernames are required")
        
#         if request.max_posts > 100 or request.max_posts < 1:
#             request.max_posts = 50
#         if request.max_stories > 50 or request.max_stories < 1:
#             request.max_stories = 25
        
#         analyzer = InstagramAnalyzer(use_credentials=request.use_credentials)
        
#         result = analyzer.analyze_interactions(
#             user1=request.user1,
#             user2=request.user2,
#             max_posts=request.max_posts,
#             max_stories=request.max_stories
#         )
        
#         if result.get("status") == "error":
#             raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed"))
        
#         return result
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @app.get("/analyze/{user1}/{user2}")
# async def analyze_interactions_get(user1: str, user2: str, use_credentials: bool = False):
#     """
#     Analyze interactions via GET request
#     """
#     try:
#         if not user1 or not user2:
#             raise HTTPException(status_code=400, detail="Both usernames are required")
        
#         analyzer = InstagramAnalyzer(use_credentials=use_credentials)
        
#         result = analyzer.analyze_interactions(
#             user1=user1,
#             user2=user2
#         )
        
#         if result.get("status") == "error":
#             raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed"))
        
#         return result
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Unexpected error in GET: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @app.exception_handler(Exception)
# async def global_exception_handler(request, exc):
#     logger.error(f"Global exception: {exc}")
#     return JSONResponse(
#         status_code=500,
#         content={"detail": "Internal server error", "error": str(exc)}
#     )

# if __name__ == "__main__":
#     uvicorn.run(
#         "app.main:app",
#         host=Config.API_HOST,
#         port=Config.API_PORT,
#         reload=True,
#         log_level="info"
#     )