@echo off
echo ========================================
echo 构建 JaCoCo Scanner Docker 镜像
echo ========================================

REM 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未安装或未启动
    echo 请安装 Docker Desktop 并确保服务正在运行
    pause
    exit /b 1
)

echo ✓ Docker 可用

REM 检查必要文件
if not exist "docker\Dockerfile.jacoco-scanner" (
    echo ❌ 缺少 Dockerfile
    pause
    exit /b 1
)

if not exist "maven-configs\jacoco-pom-overlay.xml" (
    echo ❌ 缺少 Maven 配置文件
    pause
    exit /b 1
)

if not exist "docker\scripts\scan.sh" (
    echo ❌ 缺少扫描脚本
    pause
    exit /b 1
)

echo ✓ 所有必要文件存在

echo.
echo 🔨 开始构建 Docker 镜像...
echo 镜像名称: jacoco-scanner:latest
echo.

REM 构建镜像
docker build -f docker/Dockerfile.jacoco-scanner -t jacoco-scanner:latest .

if %errorlevel% equ 0 (
    echo.
    echo ✅ Docker 镜像构建成功！
    echo.
    echo 📋 镜像信息:
    docker images jacoco-scanner:latest
    echo.
    echo 🧪 测试镜像:
    docker run --rm jacoco-scanner:latest echo "Hello from JaCoCo Scanner"
    echo.
    echo 🚀 现在可以使用 JaCoCo 扫描功能了！
) else (
    echo.
    echo ❌ Docker 镜像构建失败
    echo 请检查错误信息并重试
)

pause
