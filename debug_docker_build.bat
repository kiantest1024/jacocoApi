@echo off
echo ========================================
echo Docker 构建调试脚本
echo ========================================

REM 检查Docker状态
echo 🔍 检查Docker状态...
docker version
if %errorlevel% neq 0 (
    echo ❌ Docker 未运行
    pause
    exit /b 1
)

echo ✅ Docker 运行正常
echo.

REM 测试网络连接
echo 🌐 测试网络连接...
docker run --rm alpine ping -c 3 8.8.8.8
if %errorlevel% neq 0 (
    echo ❌ 网络连接失败
    pause
    exit /b 1
)

echo ✅ 网络连接正常
echo.

REM 测试DNS解析
echo 🔍 测试DNS解析...
docker run --rm alpine nslookup deb.debian.org
if %errorlevel% neq 0 (
    echo ❌ DNS解析失败
    pause
    exit /b 1
)

echo ✅ DNS解析正常
echo.

REM 清理旧镜像
echo 🧹 清理旧镜像...
docker rmi jacoco-scanner:latest 2>nul
echo 清理完成
echo.

REM 尝试构建基础镜像测试
echo 🧪 测试基础镜像...
docker run --rm maven:3.8.6-openjdk-11-slim echo "Base image works"
if %errorlevel% neq 0 (
    echo ❌ 基础镜像有问题
    pause
    exit /b 1
)

echo ✅ 基础镜像正常
echo.

REM 检查构建文件
echo 📋 检查构建文件...
if not exist "docker\Dockerfile.jacoco-scanner" (
    echo ❌ 缺少 Dockerfile
    pause
    exit /b 1
)

if not exist "maven-configs\jacoco-pom-overlay.xml" (
    echo ❌ 缺少 Maven 配置
    pause
    exit /b 1
)

if not exist "docker\scripts\scan.sh" (
    echo ❌ 缺少扫描脚本
    pause
    exit /b 1
)

echo ✅ 所有文件存在
echo.

REM 开始构建
echo 🔨 开始构建 Docker 镜像...
echo 使用详细输出模式
echo.

docker build --no-cache --progress=plain -f docker/Dockerfile.jacoco-scanner -t jacoco-scanner:latest .

if %errorlevel% equ 0 (
    echo.
    echo ✅ 构建成功！
    echo.
    echo 📋 镜像信息:
    docker images jacoco-scanner:latest
    echo.
    echo 🧪 测试镜像:
    docker run --rm jacoco-scanner:latest echo "JaCoCo Scanner Ready"
) else (
    echo.
    echo ❌ 构建失败
    echo.
    echo 💡 尝试简化版本构建:
    echo docker build -f Dockerfile.simple -t jacoco-scanner:latest .
)

pause
