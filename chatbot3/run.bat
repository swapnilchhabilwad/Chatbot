@echo off

echo Starting Excel evaluation pipeline...

call "%~dp0.venv\Scripts\activate.bat"

python "%~dp0run_pipeline.py"

pause
