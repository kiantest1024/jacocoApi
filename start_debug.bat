@echo off
REM JaCoCo API 调试版本启动脚本 (Windows)

echo 🔍 JaCoCo API 调试版本启动脚本
echo ================================

REM 检查Python环境
echo 💡 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装或不在PATH中
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python版本: %PYTHON_VERSION%

REM 检查当前目录
if not exist "app_debug.py" (
    if not exist "config\config.py" (
        echo ❌ 请在jacocoApi项目根目录下运行此脚本
        pause
        exit /b 1
    )
)

REM 检查依赖
echo 💡 检查Python依赖...
if exist "requirements.txt" (
    echo 💡 安装依赖包...
    python -m pip install -r requirements.txt
    echo ✅ 依赖安装完成
) else (
    echo ⚠️  未找到requirements.txt文件
)

REM 检查端口
echo 💡 检查端口8003...
netstat -an | findstr ":8003" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  端口8003已被占用
    echo 💡 请手动关闭占用端口的程序或使用其他端口
) else (
    echo ✅ 端口8003可用
)

REM 清理旧日志
echo 💡 清理旧的调试日志...
if exist "jacoco_debug.log" (
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set mydate=%%c%%a%%b
    for /f "tokens=1-2 delims=/:" %%a in ('time /t') do set mytime=%%a%%b
    set mytime=%mytime: =0%
    ren "jacoco_debug.log" "jacoco_debug_%mydate%_%mytime%.log.bak"
    echo 💡 旧日志已备份
)
echo ✅ 日志清理完成

REM 设置环境变量
echo 💡 设置调试环境变量...
set CONFIG_STORAGE_TYPE=file
set JACOCO_DEBUG_MODE=true
set JACOCO_VERBOSE_LOGGING=true
set PYTHONPATH=%PYTHONPATH%;%CD%

echo ✅ 环境变量设置完成
echo 💡 CONFIG_STORAGE_TYPE: %CONFIG_STORAGE_TYPE%
echo 💡 JACOCO_DEBUG_MODE: %JACOCO_DEBUG_MODE%
echo 💡 JACOCO_VERBOSE_LOGGING: %JACOCO_VERBOSE_LOGGING%

REM 显示调试信息
echo.
echo 💡 调试版本信息:
echo   🔍 调试模式: 启用
echo   📝 详细日志: 启用
echo   🌐 服务端口: 8003
echo   📄 日志文件: jacoco_debug.log
echo   🔗 服务地址: http://localhost:8003
echo   📖 API文档: http://localhost:8003/docs
echo   🔍 调试日志: http://localhost:8003/debug/logs
echo.

REM 检查调试应用文件
if not exist "app_debug.py" (
    echo ❌ 调试应用文件app_debug.py不存在
    pause
    exit /b 1
)

echo ✅ 开始启动调试服务...
echo ⚠️  按 Ctrl+C 停止服务
echo.

REM 启动应用
python app_debug.py

echo.
echo 🔚 调试服务已停止
pause
