import logging
import time
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from jacoco_tasks import celery_app
from security import verify_api_key, create_security_middleware
from logging_config import setup_logging
from api_endpoints import router as api_router
from github_webhook import router as github_router

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(github_router)
app.middleware("http")(create_security_middleware())

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "timestamp": time.time()
    }

@app.get("/task/{task_id}", dependencies=[Depends(verify_api_key)])
async def get_task_status(task_id: str):
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {"status": "pending", "task_id": task_id}
        elif task.state == 'STARTED':
            response = {"status": "started", "task_id": task_id}
        elif task.state == 'SUCCESS':
            response = {"status": "completed", "task_id": task_id, "result": task.result}
        elif task.state == 'FAILURE':
            response = {"status": "failed", "task_id": task_id, "error": str(task.result)}
        else:
            response = {"status": task.state.lower(), "task_id": task_id}
        
        return JSONResponse(status_code=200, content=response)
    
    except Exception as e:
        logger.error(f"Error retrieving task status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving task status: {str(e)}")

@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=settings.DEBUG)
