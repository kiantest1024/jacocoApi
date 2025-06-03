@echo off
REM Docker 镜像构建脚本 (Windows)
REM 构建 JaCoCo 扫描器 Docker 镜像

setlocal enabledelayedexpansion

REM 配置
set IMAGE_NAME=jacoco-scanner
set IMAGE_TAG=latest
set DOCKERFILE_PATH=docker\Dockerfile.jacoco-scanner

echo ==========================================
echo 构建 JaCoCo 扫描器 Docker 镜像
echo ==========================================
echo 镜像名称: %IMAGE_NAME%:%IMAGE_TAG%
echo Dockerfile: %DOCKERFILE_PATH%
echo ==========================================

REM 检查 Docker 是否可用
docker --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker 未安装或不在 PATH 中
    exit /b 1
)

REM 检查 Dockerfile 是否存在
if not exist "%DOCKERFILE_PATH%" (
    echo 错误: Dockerfile 不存在: %DOCKERFILE_PATH%
    exit /b 1
)

REM 检查必要的文件
echo 检查必要的文件...

set REQUIRED_FILES=maven-configs\jacoco-pom-overlay.xml docker\scripts\scan.sh docker\scripts\generate-enhanced-pom.sh docker\scripts\generate-summary.sh

for %%f in (%REQUIRED_FILES%) do (
    if not exist "%%f" (
        echo 错误: 必需文件不存在: %%f
        exit /b 1
    )
    echo ✓ %%f
)

REM 构建 Docker 镜像
echo 开始构建 Docker 镜像...
docker build -t "%IMAGE_NAME%:%IMAGE_TAG%" -f "%DOCKERFILE_PATH%" .

if errorlevel 1 (
    echo ✗ Docker 镜像构建失败
    exit /b 1
)

echo ✓ Docker 镜像构建成功: %IMAGE_NAME%:%IMAGE_TAG%

REM 显示镜像信息
echo ==========================================
echo 镜像信息:
docker images "%IMAGE_NAME%:%IMAGE_TAG%"

echo ==========================================
echo 构建完成!
echo ==========================================
echo 使用方法:
echo   docker run --rm -v %cd%\reports:/app/reports ^
echo     %IMAGE_NAME%:%IMAGE_TAG% ^
echo     --repo-url https://github.com/user/repo.git ^
echo     --commit-id abc123 ^
echo     --branch main
echo ==========================================

pause
