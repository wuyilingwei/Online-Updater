@echo off
title Builder
pip install -r requirements.txt
pyinstaller main.spec
if %errorlevel% neq 0 (
    echo Error: Build failed
    echo Check the error message above
    pause
    exit
)
echo Build successful
echo Check the dist folder for the executable
echo Builder will close in 10 seconds, press any key to exit now
timeout /t 10
exit 