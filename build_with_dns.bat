@echo off
echo ========================================
echo 使用DNS配置构建Docker镜像
echo ========================================

echo 🔧 尝试多种构建方案...
echo.

REM 方案1: 使用国内镜像源
echo 📋 方案1: 使用国内镜像源构建...
docker build --dns=8.8.8.8 --dns=114.114.114.114 -f Dockerfile.china -t jacoco-scanner:latest .

if %errorlevel% equ 0 (
    echo ✅ 方案1成功！
    goto :success
)

echo ❌ 方案1失败，尝试方案2...
echo.

REM 方案2: 使用预装工具的镜像
echo 📋 方案2: 使用预装工具镜像构建...
docker build --dns=8.8.8.8 --dns=114.114.114.114 -f Dockerfile.prebuilt -t jacoco-scanner:latest .

if %errorlevel% equ 0 (
    echo ✅ 方案2成功！
    goto :success
)

echo ❌ 方案2失败，尝试方案3...
echo.

REM 方案3: 使用简化版本
echo 📋 方案3: 使用简化版本构建...
docker build --dns=8.8.8.8 --dns=114.114.114.114 -f Dockerfile.simple -t jacoco-scanner:latest .

if %errorlevel% equ 0 (
    echo ✅ 方案3成功！
    goto :success
)

echo ❌ 所有方案都失败了
echo.
echo 💡 建议：
echo 1. 检查网络连接
echo 2. 配置Docker DNS设置
echo 3. 使用本地扫描模式（已配置）
echo.
echo 🚀 本地扫描模式已启用，可以直接使用：
echo python3 app.py
goto :end

:success
echo.
echo 🎉 Docker镜像构建成功！
echo.
echo 📋 镜像信息:
docker images jacoco-scanner:latest
echo.
echo 🧪 测试镜像:
docker run --rm jacoco-scanner:latest echo "JaCoCo Scanner Ready"
echo.
echo 🚀 现在可以使用Docker扫描模式了！

:end
pause
