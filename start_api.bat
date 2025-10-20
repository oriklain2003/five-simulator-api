@echo off
echo ================================================================
echo Starting Simulation API Server
echo ================================================================
echo.
echo Installing/Updating dependencies...
pip install -r requirements.txt
echo.
echo Starting server on http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ================================================================
echo.
python main.py

