@echo off
REM JaCoCo Scanner Docker镜像构建脚本 (Windows)

echo 🐳 构建JaCoCo Scanner Docker镜像...

REM 检查Docker是否可用
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未安装或不在PATH中
    exit /b 1
)

REM 检查Docker守护进程是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker守护进程未运行
    exit /b 1
)

REM 检查必要文件是否存在
if not exist "docker\Dockerfile" (
    echo ❌ 未找到Dockerfile: docker\Dockerfile
    exit /b 1
)

if not exist "docker\scripts" (
    echo ❌ 未找到脚本目录: docker\scripts
    exit /b 1
)

REM 构建镜像
echo 📦 开始构建Docker镜像...
docker build -t jacoco-scanner:latest -f docker\Dockerfile docker\

if %errorlevel% equ 0 (
    echo ✅ Docker镜像构建成功: jacoco-scanner:latest
    
    REM 显示镜像信息
    echo.
    echo 📋 镜像信息:
    docker images jacoco-scanner:latest
    
    echo.
    echo 🎉 构建完成！现在可以使用Docker扫描模式了。
    echo.
    echo 💡 使用说明:
    echo    - 服务将优先使用Docker扫描
    echo    - 如果Docker不可用，会自动回退到本地扫描
    echo    - 可以通过配置强制使用本地扫描
) else (
    echo ❌ Docker镜像构建失败
    exit /b 1
)
