import logging
import time
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# 简化配置以避免导入问题
class Settings:
    API_TITLE = "Universal JaCoCo Scanner API"
    API_DESCRIPTION = "Universal JaCoCo coverage scanner for any Maven project"
    API_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

settings = Settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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

# 直接加载路由
try:
    from api_endpoints import router as api_router
    from github_webhook import router as github_router

    app.include_router(api_router)
    app.include_router(github_router)
    logger.info("✅ Routers loaded successfully")
except Exception as e:
    logger.warning(f"⚠️ Failed to load some routers: {e}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "timestamp": time.time()
    }

@app.get("/")
async def root():
    return {
        "message": "Universal JaCoCo Scanner API is running",
        "version": settings.API_VERSION,
        "docs": "/docs"
    }

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
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=settings.DEBUG)
