@echo off
echo Starting Streamlit app...
call "%~dp0ragenv\Scripts\activate.bat"
"%~dp0ragenv\Scripts\python.exe" -m streamlit run "%~dp0app.py"
pause
