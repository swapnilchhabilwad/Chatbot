@echo off

echo Starting Hybrid Chatbot System...

call "%~dp0ragenv\Scripts\activate.bat"

streamlit run app.py

pause