@echo off
echo Starting Forge - AI Experimentation Substrate
echo ===========================================
echo.
cd /d "%~dp0"
docker compose -f docker\docker-compose.yml up --build -d
echo.
if %errorlevel% equ 0 (
    echo Forge is running!
    echo API: http://localhost:8000
    echo Docs: http://localhost:8000/docs
) else (
    echo Failed to start Forge.
)
