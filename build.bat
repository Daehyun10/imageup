@echo off
chcp 65001 >nul
setlocal

echo [1/3] 빌드 도구 설치
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto fail

echo [2/3] exe 빌드
python -m PyInstaller --noconfirm --noconsole --onefile --name ImageOverlay overlay.py
if errorlevel 1 goto fail

echo [3/3] 완료
echo 만들어진 파일: %cd%\dist\ImageOverlay.exe
explorer "%cd%\dist"
pause
exit /b 0

:fail
echo.
echo 빌드에 실패했습니다. 위 메시지를 확인하세요.
echo Python이 설치되어 있는지 확인: python --version
pause
exit /b 1
