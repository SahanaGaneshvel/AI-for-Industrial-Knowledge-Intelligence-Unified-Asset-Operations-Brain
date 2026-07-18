@echo off
echo Starting AssetBrain Backend...
echo.

REM Check if GEMINI_API_KEY is set
if "%GEMINI_API_KEY%"=="" (
    echo ERROR: GEMINI_API_KEY environment variable not set
    echo Please set it with: set GEMINI_API_KEY=your-key-here
    pause
    exit /b 1
)

echo GEMINI_API_KEY is set
echo.

REM Navigate to project root
cd /d "%~dp0\.."

echo Starting FastAPI server on http://localhost:8000
echo.
uvicorn backend.main:app --reload --port 8000
