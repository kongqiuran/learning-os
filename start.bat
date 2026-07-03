@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Starting ExamPilot...
python -m streamlit run app.py

echo.
echo ExamPilot stopped or failed to start. Please take a screenshot if there is an error.
pause
