@echo off
REM Personal Media Visualization 실행 스크립트 (Windows)
REM
REM 사용법:
REM   run.bat [명령어]
REM
REM 명령어:
REM   server    - API 서버 시작 (기본값)
REM   dev       - 개발 모드로 서버 시작 (자동 리로드)
REM   test      - 테스트 실행
REM   lint      - 코드 품질 검사
REM   install   - 의존성 설치
REM   help      - 도움말 표시

setlocal enabledelayedexpansion

REM 프로젝트 루트 디렉토리
cd /d "%~dp0"

REM 기본 설정
if "%PMV_HOST%"=="" set PMV_HOST=0.0.0.0
if "%PMV_PORT%"=="" set PMV_PORT=8000
if "%PYTHON%"=="" set PYTHON=python

REM 명령어 분기
if "%1"=="" goto server
if "%1"=="server" goto server
if "%1"=="dev" goto dev
if "%1"=="test" goto test
if "%1"=="lint" goto lint
if "%1"=="install" goto install
if "%1"=="install-dev" goto install_dev
if "%1"=="help" goto help
if "%1"=="--help" goto help
if "%1"=="-h" goto help

echo [ERROR] 알 수 없는 명령어: %1
goto help

:logo
echo ==================================================
echo    Personal Media Visualization
echo    오디오 분석 및 시각화 시스템
echo ==================================================
echo.
goto :eof

:check_python
where %PYTHON% >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되어 있지 않습니다.
    exit /b 1
)
for /f "tokens=2" %%i in ('%PYTHON% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Python 버전: %PYTHON_VERSION%
goto :eof

:activate_venv
if exist "venv\Scripts\activate.bat" (
    echo [INFO] 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo [INFO] 가상환경 활성화 중...
    call .venv\Scripts\activate.bat
)
goto :eof

:create_dirs
if not exist "data\uploads" mkdir data\uploads
if not exist "data\cache" mkdir data\cache
if not exist "output\renders" mkdir output\renders
if not exist "output\exports" mkdir output\exports
if not exist "temp" mkdir temp
if not exist "logs" mkdir logs
goto :eof

:server
call :logo
call :check_python
call :activate_venv
call :create_dirs

echo [INFO] API 서버 시작 중...
echo [INFO] 주소: http://%PMV_HOST%:%PMV_PORT%
echo [INFO] 웹 인터페이스: http://%PMV_HOST%:%PMV_PORT%/web
echo [INFO] API 문서: http://%PMV_HOST%:%PMV_PORT%/docs
echo.
echo [INFO] 종료하려면 Ctrl+C를 누르세요.
echo.

%PYTHON% run_api_server.py
goto end

:dev
call :logo
call :check_python
call :activate_venv
call :create_dirs

echo [INFO] 개발 모드로 API 서버 시작 중...
echo [INFO] 주소: http://%PMV_HOST%:%PMV_PORT%
echo [INFO] 웹 인터페이스: http://%PMV_HOST%:%PMV_PORT%/web
echo [INFO] API 문서: http://%PMV_HOST%:%PMV_PORT%/docs
echo.
echo [INFO] 종료하려면 Ctrl+C를 누르세요.
echo.

%PYTHON% -m uvicorn src.api.app:app --host %PMV_HOST% --port %PMV_PORT% --reload
goto end

:test
call :check_python
call :activate_venv

echo [INFO] 테스트 실행 중...
%PYTHON% -m pytest tests/ -v
goto end

:lint
call :check_python
call :activate_venv

echo [INFO] 코드 품질 검사 중...
echo [INFO] Black 포매팅 검사...
%PYTHON% -m black --check src tests 2>nul
echo [INFO] Ruff 린팅...
%PYTHON% -m ruff check src tests 2>nul
echo [INFO] 코드 품질 검사 완료
goto end

:install
call :check_python
call :activate_venv

echo [INFO] 의존성 설치 중...
%PYTHON% -m pip install -r requirements.txt
echo [INFO] 의존성 설치 완료
goto end

:install_dev
call :check_python
call :activate_venv

echo [INFO] 개발 의존성 설치 중...
%PYTHON% -m pip install -r requirements-dev.txt
echo [INFO] 개발 의존성 설치 완료
goto end

:help
echo Personal Media Visualization 실행 스크립트
echo.
echo 사용법: run.bat [명령어]
echo.
echo 명령어:
echo   server    API 서버 시작 (기본값)
echo   dev       개발 모드로 서버 시작 (자동 리로드)
echo   test      테스트 실행
echo   lint      코드 품질 검사
echo   install   의존성 설치
echo   help      이 도움말 표시
echo.
echo 환경 변수:
echo   PMV_HOST  서버 호스트 (기본값: 0.0.0.0)
echo   PMV_PORT  서버 포트 (기본값: 8000)
echo   PYTHON    Python 실행 파일 (기본값: python)
echo.
echo 예시:
echo   run.bat                    서버 시작
echo   run.bat dev                개발 모드
echo   set PMV_PORT=9000 ^&^& run.bat   포트 9000에서 시작
goto end

:end
endlocal
