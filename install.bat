@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Checking Python...
python --version >nul 2>nul
if errorlevel 1 (
    echo Python is not available. Please install Python 3.10 or newer first.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed. Please take a screenshot of this window.
    pause
    exit /b 1
)

echo.
echo 安装完成，可以双击 start.bat 启动
pause
