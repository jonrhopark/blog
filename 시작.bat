@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo.
echo  블로그 자동화 시스템 시작...
echo.

REM Python 확인
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo  [오류] Python이 설치되어 있지 않습니다.
    echo  https://python.org 에서 Python 3.10 이상을 설치하세요.
    pause
    exit /b 1
)

REM 패키지 설치 확인
python -c "import anthropic" > nul 2>&1
if %errorlevel% neq 0 (
    echo  패키지 설치 중...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo  [오류] 패키지 설치에 실패했습니다.
        echo  관리자 권한으로 실행하거나 아래 명령을 직접 실행해 보세요:
        echo    pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo.
)

REM .env 파일 확인
if not exist ".env" (
    echo  [안내] .env 파일이 없습니다.
    echo  .env.example을 복사해서 .env로 만들고,
    echo  ANTHROPIC_API_KEY를 입력해주세요.
    echo.
    copy .env.example .env
    notepad .env
)

REM GUI 실행
echo  GUI 실행 중...
python gui.py 2>startup_error.txt
set EXIT_CODE=%errorlevel%

if %EXIT_CODE% neq 0 (
    echo.
    echo  ================================================
    echo  [오류] GUI 시작에 실패했습니다.
    echo  ================================================
    if exist startup_error.txt (
        echo.
        echo  --- 오류 내용 ---
        type startup_error.txt
    )
    if exist error_log.txt (
        echo.
        echo  --- 상세 오류 (error_log.txt) ---
        type error_log.txt
    )
    echo.
    pause
)
