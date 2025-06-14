@echo off
echo ========================================
echo Products Finder - Chunked Version
echo ========================================
echo.

echo Starting FastAPI server (chunked)...
start "FastAPI Chunked" cmd /k "python main.py"

echo Waiting for API to start...
timeout /t 5 /nobreak > nul

echo Starting Streamlit app (chunked)...
start "Streamlit Chunked" cmd /k "streamlit run streamlit_app.py --server.port 8502"

echo.
echo ========================================
echo Both applications are starting...
echo.
echo FastAPI (Chunked): http://localhost:8001
echo Streamlit (Chunked): http://localhost:8502
echo.
echo Press any key to close this window...
echo ========================================
pause > nul