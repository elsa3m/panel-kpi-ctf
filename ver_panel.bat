@echo off
REM ---------------------------------------------------------------
REM  Abre el Panel KPI CTF en tu computador, sin subir nada a GitHub.
REM  Basta con hacer doble clic en este archivo.
REM ---------------------------------------------------------------
cd /d "%~dp0"
echo Abriendo el Panel KPI CTF...
echo.
call .venv\Scripts\activate.bat
streamlit run app.py
echo.
echo El panel se cerro. Puedes cerrar esta ventana.
pause
