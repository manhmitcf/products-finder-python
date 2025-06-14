@echo off
echo ========================================
echo Setting up Chunked Data
echo ========================================
echo.

echo This script will:
echo 1. Load your product data
echo 2. Split long descriptions into chunks
echo 3. Generate embeddings for each chunk
echo 4. Store chunked data in MongoDB
echo.

echo WARNING: This process may take several minutes...
echo.

set /p confirm="Do you want to continue? (y/n): "
if /i "%confirm%" neq "y" (
    echo Setup cancelled.
    pause
    exit /b
)

echo.
echo Starting chunked data processing...
python load_data.py

echo.
echo ========================================
echo Setup completed!
echo.
echo Next steps:
echo 1. Create vector search index in MongoDB Atlas
echo 2. Run the chunked application: run_app.bat
echo.
echo Press any key to close...
echo ========================================
pause > nul