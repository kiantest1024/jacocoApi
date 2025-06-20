@echo off
REM JaCoCo Scanner Docker镜像构建脚本 (Windows版本)
setlocal enabledelayedexpansion

echo 🚀 开始构建 JaCoCo Scanner Docker 镜像...

REM 检查Docker是否可用
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker 未安装或不可用
    pause
    exit /b 1
)

REM 检查Docker服务是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker 服务未运行，请启动 Docker Desktop
    pause
    exit /b 1
)

REM 进入脚本目录
cd /d "%~dp0"

echo 📁 当前目录: %CD%

REM 检查必要文件
if not exist "docker\Dockerfile.alpine" (
    echo ❌ 未找到 docker\Dockerfile.alpine
    pause
    exit /b 1
)

if not exist "docker\scripts\scan.sh" (
    echo ❌ 未找到 docker\scripts\scan.sh
    pause
    exit /b 1
)

REM 构建镜像
echo 🔨 构建 jacoco-scanner:latest 镜像...
docker build -f docker\Dockerfile.alpine -t jacoco-scanner:latest docker\

REM 检查构建结果
docker images | findstr "jacoco-scanner.*latest" >nul
if errorlevel 1 (
    echo ❌ 镜像构建失败
    pause
    exit /b 1
) else (
    echo ✅ JaCoCo Scanner 镜像构建成功！
    echo.
    echo 📋 镜像信息:
    docker images | findstr jacoco-scanner
    echo.
    echo 🧪 测试镜像:
    echo docker run --rm jacoco-scanner:latest --help
)

echo.
echo 🎉 构建完成！现在可以使用 JaCoCo API 进行 Docker 扫描了。
pause
