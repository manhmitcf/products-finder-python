@echo off
echo Starting Products Finder Application...

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and fill in your MongoDB credentials.
    pause
    exit /b 1
)

echo.
echo Starting FastAPI server in background...
start "FastAPI Server" cmd /c "uvicorn main:app --host 0.0.0.0 --port 8000"

echo Waiting for API server to start...
timeout /t 5 /nobreak > nul

echo.
echo Starting Streamlit UI...
echo.
echo ========================================
echo   FastAPI Server: http://localhost:8000
echo   Streamlit UI:   http://localhost:8501
echo ========================================
echo.

streamlit run streamlit_app.py --server.port 8501

pause