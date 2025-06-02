@echo off
REM GitHub Webhook JaCoCo API 快速启动脚本 (Windows)
REM 用于快速启动 GitHub webhook 接收服务

echo ========================================
echo GitHub Webhook JaCoCo API 快速启动
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python 未安装或不在 PATH 中
    echo 请安装 Python 3.8+ 并确保在 PATH 中
    pause
    exit /b 1
)

REM 检查是否在正确的目录
if not exist "main.py" (
    echo 错误: 请在 jacocoApi 目录中运行此脚本
    echo 当前目录: %CD%
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo 错误: 创建虚拟环境失败
        pause
        exit /b 1
    )
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo 错误: 安装依赖失败
    pause
    exit /b 1
)

REM 检查环境配置文件
if not exist ".env" (
    echo 创建环境配置文件...
    copy .env.example .env
    echo.
    echo 注意: 请编辑 .env 文件配置您的 GitHub webhook 密钥
    echo.
)

REM 检查 Redis 是否运行
echo 检查 Redis 连接...
python -c "import redis; r=redis.Redis(); r.ping(); print('Redis 连接正常')" 2>nul
if errorlevel 1 (
    echo 警告: Redis 连接失败
    echo 请确保 Redis 服务正在运行
    echo 您可以使用 Docker 启动 Redis: docker run -d -p 6379:6379 redis:alpine
    echo.
)

REM 检查 Java 和 Maven
echo 检查 Java 和 Maven...
java -version >nul 2>&1
if errorlevel 1 (
    echo 警告: Java 未安装或不在 PATH 中
    echo JaCoCo 扫描需要 Java 11+
)

mvn -version >nul 2>&1
if errorlevel 1 (
    echo 警告: Maven 未安装或不在 PATH 中
    echo JaCoCo 扫描需要 Maven 3.6+
)

echo.
echo ========================================
echo 启动服务
echo ========================================
echo.

REM 启动 Celery worker (后台)
echo 启动 Celery worker...
start "Celery Worker" cmd /c "venv\Scripts\activate.bat && celery -A jacoco_tasks.celery_app worker --loglevel=info"

REM 等待一下让 Celery 启动
timeout /t 3 /nobreak >nul

REM 启动 FastAPI 服务器
echo 启动 FastAPI 服务器...
echo.
echo 服务将在以下地址启动:
echo   - API 服务: http://localhost:8001
echo   - API 文档: http://localhost:8001/docs
echo   - 健康检查: http://localhost:8001/health
echo   - GitHub Webhook: http://localhost:8001/github/webhook
echo.
echo 按 Ctrl+C 停止服务
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

echo.
echo 服务已停止
pause
