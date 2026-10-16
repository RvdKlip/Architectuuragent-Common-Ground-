@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
 echo Python Launcher ontbreekt. Installeer Python 3.11+ vanaf python.org.
 pause
 exit /b 1
)
if not exist .venv\Scripts\python.exe (
 py -3.11 -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
 echo Installatie mislukt; raadpleeg README.md.
 pause
 exit /b 1
)
streamlit run app.py
