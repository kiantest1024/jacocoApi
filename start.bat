@echo off
echo ========================================
echo Universal JaCoCo Scanner API
echo ========================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found
    pause & exit /b 1
)

python -c "import fastapi, uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Missing dependencies. Installing...
    pip install fastapi uvicorn
)

echo 🚀 Starting server on port 8002 (avoiding port conflict)
echo 📡 Server: http://localhost:8002
echo 📖 API docs: http://localhost:8002/docs
echo.

python -m uvicorn app:app --host 0.0.0.0 --port 8002 --reload
