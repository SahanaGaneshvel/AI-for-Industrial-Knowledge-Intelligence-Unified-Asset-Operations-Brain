@echo off
echo Starting AssetBrain Frontend...
echo.

cd /d "%~dp0\..\frontend"

if not exist "node_modules" (
    echo Installing npm dependencies...
    call npm install
    echo.
)

echo Starting Vite dev server on http://localhost:5173
echo.
npm run dev
