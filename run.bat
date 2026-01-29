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
REM   format    - 코드 포매팅
REM   check     - lint + type check
REM   install   - 의존성 설치
REM   build     - 프로젝트 빌드/패키징
REM   clean     - 캐시 및 임시 파일 정리
REM   docs      - 문서 생성
REM   benchmark - 벤치마크 실행
REM   coverage  - 커버리지 리포트 생성
REM   info      - 시스템 정보 출력
REM   help      - 도움말 표시
REM

setlocal enabledelayedexpansion

REM Windows 10+ ANSI 색상 지원 활성화
for /F "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
if "%version%" == "10.0" (
    REM Windows 10/11 - ANSI 색상 지원
    set "ESC="
    set "RED=[91m"
    set "GREEN=[92m"
    set "YELLOW=[93m"
    set "BLUE=[94m"
    set "MAGENTA=[95m"
    set "CYAN=[96m"
    set "BOLD=[1m"
    set "NC=[0m"
) else (
    REM 이전 버전 - 색상 없음
    set "ESC="
    set "RED="
    set "GREEN="
    set "YELLOW="
    set "BLUE="
    set "MAGENTA="
    set "CYAN="
    set "BOLD="
    set "NC="
)

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
if "%1"=="format" goto format
if "%1"=="check" goto check
if "%1"=="install" goto install
if "%1"=="install-dev" goto install_dev
if "%1"=="build" goto build
if "%1"=="clean" goto clean
if "%1"=="docs" goto docs
if "%1"=="benchmark" goto benchmark
if "%1"=="coverage" goto coverage
if "%1"=="info" goto info
if "%1"=="help" goto help
if "%1"=="--help" goto help
if "%1"=="-h" goto help

echo %RED%[ERROR]%NC% 알 수 없는 명령어: %1
echo.
goto help

:logo
echo %CYAN%
echo   ____  __  ____   __
echo  ^|  _ \^|  \/  \ \ / /
echo  ^| ^|_^) ^| ^|\/^| ^|\ V /
echo  ^|  __/^| ^|  ^| ^| ^| ^|
echo  ^|_^|   ^|_^|  ^|_^| ^|_^|
echo %NC%
echo %BOLD%Personal Media Visualization%NC%
echo %BLUE%Audio Analysis ^& Visualization System%NC%
echo.
echo %MAGENTA%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%NC%
echo.
goto :eof

:check_python
where %PYTHON% >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Python이 설치되어 있지 않습니다.
    exit /b 1
)
for /f "tokens=2" %%i in ('%PYTHON% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %GREEN%[INFO]%NC% Python 버전: %PYTHON_VERSION%
goto :eof

:activate_venv
if exist "venv\Scripts\activate.bat" (
    echo %GREEN%[INFO]%NC% 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo %GREEN%[INFO]%NC% 가상환경 활성화 중...
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

echo %BOLD%API 서버 시작%NC%
echo.
echo %GREEN%[INFO]%NC% 주소: http://%PMV_HOST%:%PMV_PORT%
echo %GREEN%[INFO]%NC% 웹 인터페이스: http://%PMV_HOST%:%PMV_PORT%/web
echo %GREEN%[INFO]%NC% API 문서: http://%PMV_HOST%:%PMV_PORT%/docs
echo.
echo %GREEN%[INFO]%NC% 종료하려면 Ctrl+C를 누르세요.
echo.

%PYTHON% run_api_server.py
goto end

:dev
call :logo
call :check_python
call :activate_venv
call :create_dirs

echo %BOLD%개발 모드 서버 시작%NC%
echo.
echo %GREEN%[INFO]%NC% 주소: http://%PMV_HOST%:%PMV_PORT%
echo %GREEN%[INFO]%NC% 웹 인터페이스: http://%PMV_HOST%:%PMV_PORT%/web
echo %GREEN%[INFO]%NC% API 문서: http://%PMV_HOST%:%PMV_PORT%/docs
echo.
echo %GREEN%[INFO]%NC% 자동 리로드 활성화
echo %GREEN%[INFO]%NC% 종료하려면 Ctrl+C를 누르세요.
echo.

%PYTHON% -m uvicorn src.api.app:app --host %PMV_HOST% --port %PMV_PORT% --reload
goto end

:test
call :check_python
call :activate_venv

echo %GREEN%[INFO]%NC% 테스트 실행 중...
echo.

if "%2"=="" (
    %PYTHON% -m pytest tests/ -v --cov=src --cov-report=term-missing
) else (
    %PYTHON% -m pytest %2 %3 %4 %5 %6 %7 %8 %9
)
goto end

:lint
call :check_python
call :activate_venv

echo %GREEN%[INFO]%NC% 코드 품질 검사 중...
echo.

echo %CYAN%[...]%NC% Ruff 린팅 검사...
%PYTHON% -m ruff check src tests
if errorlevel 1 (
    echo %YELLOW%[WARN]%NC% Ruff 검사에서 문제 발견
) else (
    echo %GREEN%[OK]%NC% Ruff 검사 통과
)

echo %CYAN%[...]%NC% Black 포매팅 검사...
%PYTHON% -m black --check src tests
if errorlevel 1 (
    echo %YELLOW%[WARN]%NC% Black 검사에서 문제 발견
) else (
    echo %GREEN%[OK]%NC% Black 검사 통과
)

echo.
echo %GREEN%[INFO]%NC% 코드 품질 검사 완료
goto end

:format
call :check_python
call :activate_venv

echo %GREEN%[INFO]%NC% 코드 포매팅 중...
echo.

echo %CYAN%[...]%NC% Black으로 포매팅...
%PYTHON% -m black src tests
echo %GREEN%[OK]%NC% 포매팅 완료

echo %CYAN%[...]%NC% Ruff로 자동 수정...
%PYTHON% -m ruff check --fix src tests 2>nul
echo %GREEN%[OK]%NC% 린트 수정 완료
goto end

:check
call :check_python
call :activate_venv

echo %GREEN%[INFO]%NC% 전체 검사 실행 중...
echo.

call :lint

echo %CYAN%[...]%NC% MyPy 타입 검사...
%PYTHON% -m mypy src --ignore-missing-imports
if errorlevel 1 (
    echo %YELLOW%[WARN]%NC% 타입 검사에서 경고/오류 발생
) else (
    echo %GREEN%[OK]%NC% 타입 검사 통과
)

echo.
echo %GREEN%[OK]%NC% 전체 검사 완료
goto end

:install
call :check_python
call :activate_venv

echo %GREEN%[INFO]%NC% 의존성 설치 중...
%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install -r requirements.txt
echo %GREEN%[OK]%NC% 의존성 설치 완료
goto end

:install_dev
call :check_python
call :activate_venv

echo %GREEN%[INFO]%NC% 개발 의존성 설치 중...
%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install -r requirements.txt
%PYTHON% -m pip install -r requirements-dev.txt
echo %GREEN%[OK]%NC% 개발 의존성 설치 완료
goto end

:build
call :check_python
call :activate_venv

echo %GREEN%[INFO]%NC% 프로젝트 빌드 중...
echo.

if exist "pyproject.toml" (
    echo %CYAN%[...]%NC% 패키지 빌드...
    %PYTHON% -m pip install build
    %PYTHON% -m build
    echo %GREEN%[OK]%NC% 빌드 완료 - dist\ 디렉토리 확인
) else if exist "setup.py" (
    echo %CYAN%[...]%NC% 패키지 빌드...
    %PYTHON% -m pip install build
    %PYTHON% -m build
    echo %GREEN%[OK]%NC% 빌드 완료 - dist\ 디렉토리 확인
) else (
    echo %YELLOW%[WARN]%NC% pyproject.toml 또는 setup.py를 찾을 수 없습니다.
)
goto end

:clean
echo %GREEN%[INFO]%NC% 정리 중...
echo.

echo %CYAN%[...]%NC% Python 캐시 삭제...
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul

echo %CYAN%[...]%NC% 테스트/빌드 캐시 삭제...
if exist ".pytest_cache" rd /s /q ".pytest_cache" 2>nul
if exist ".mypy_cache" rd /s /q ".mypy_cache" 2>nul
if exist ".ruff_cache" rd /s /q ".ruff_cache" 2>nul
if exist ".coverage" del /q ".coverage" 2>nul
if exist "htmlcov" rd /s /q "htmlcov" 2>nul
if exist "build" rd /s /q "build" 2>nul
if exist "dist" rd /s /q "dist" 2>nul
for /d %%d in (*.egg-info) do rd /s /q "%%d" 2>nul

echo %CYAN%[...]%NC% 임시 파일 삭제...
if exist "temp" del /q "temp\*" 2>nul

echo %GREEN%[OK]%NC% 정리 완료
goto end

:docs
call :check_python
call :activate_venv

echo %GREEN%[INFO]%NC% 문서 생성 중...
echo.

if exist "docs" (
    %PYTHON% -m mkdocs build 2>nul
    if errorlevel 1 (
        echo %YELLOW%[WARN]%NC% MkDocs를 찾을 수 없습니다. Sphinx 시도...
        sphinx-build -b html docs docs\_build\html 2>nul
        if errorlevel 1 (
            echo %YELLOW%[WARN]%NC% 문서 생성 도구를 찾을 수 없습니다.
        ) else (
            echo %GREEN%[OK]%NC% 문서 생성 완료 - docs\_build\html\ 확인
        )
    ) else (
        echo %GREEN%[OK]%NC% 문서 생성 완료 - site\ 디렉토리 확인
    )
) else (
    echo %YELLOW%[WARN]%NC% docs 디렉토리를 찾을 수 없습니다.
)
goto end

:benchmark
call :check_python
call :activate_venv

echo %GREEN%[INFO]%NC% 벤치마크 실행 중...
echo.

if exist "tests\benchmarks" (
    %PYTHON% -m pytest tests\benchmarks\ --benchmark-only -v
) else (
    echo %YELLOW%[WARN]%NC% 벤치마크 디렉토리를 찾을 수 없습니다.
)
goto end

:coverage
call :check_python
call :activate_venv

echo %GREEN%[INFO]%NC% 커버리지 리포트 생성 중...
echo.

%PYTHON% -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
echo %GREEN%[OK]%NC% 커버리지 리포트 생성 완료 - htmlcov\index.html 확인
goto end

:info
call :logo

echo %BOLD%시스템 정보%NC%
echo.

REM Python 정보
where %PYTHON% >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%v in ('%PYTHON% --version 2^>^&1') do echo Python:        %%v
    for /f "tokens=*" %%p in ('where %PYTHON%') do echo Python 경로:   %%p
)
echo.

REM 환경 정보
echo %BOLD%환경%NC%
echo OS:            Windows
for /f "tokens=4-5 delims=. " %%i in ('ver') do echo 버전:          %%i.%%j
echo.

REM 프로젝트 정보
echo %BOLD%프로젝트%NC%
echo 경로:          %cd%

if exist "src\__init__.py" (
    for /f "tokens=*" %%v in ('%PYTHON% -c "from src import __version__; print(__version__)" 2^>nul') do echo 버전:          %%v
)
echo.

REM 가상환경 정보
echo %BOLD%가상환경%NC%
if exist "venv" (
    echo 위치:          venv\
) else if exist ".venv" (
    echo 위치:          .venv\
) else (
    echo 상태:          감지되지 않음
)
echo.
goto end

:help
call :logo

echo %BOLD%사용법:%NC% run.bat [명령어] [옵션]
echo.
echo %BOLD%서버 명령어:%NC%
echo   server      API 서버 시작 (기본값)
echo   dev         개발 모드로 서버 시작 (자동 리로드)
echo.
echo %BOLD%개발 명령어:%NC%
echo   test        테스트 실행
echo   lint        코드 품질 검사 (ruff, black --check)
echo   format      코드 포매팅 (black, ruff --fix)
echo   check       전체 검사 (lint + type check)
echo   coverage    커버리지 리포트 생성
echo   benchmark   벤치마크 실행
echo.
echo %BOLD%빌드 명령어:%NC%
echo   install     의존성 설치
echo   install-dev 개발 의존성 설치
echo   build       프로젝트 빌드/패키징
echo   clean       캐시 및 임시 파일 정리
echo   docs        문서 생성
echo.
echo %BOLD%유틸리티:%NC%
echo   info        시스템 정보 출력
echo   help        이 도움말 표시
echo.
echo %BOLD%환경 변수:%NC%
echo   PMV_HOST    서버 호스트 (기본값: 0.0.0.0)
echo   PMV_PORT    서버 포트 (기본값: 8000)
echo   PYTHON      Python 실행 파일 (기본값: python)
echo.
echo %BOLD%예시:%NC%
echo   run.bat                       서버 시작
echo   run.bat dev                   개발 모드
echo   run.bat test -k player        'player' 키워드 테스트만 실행
echo   set PMV_PORT=9000 ^&^& run.bat  포트 9000에서 시작
echo.
goto end

:end
endlocal
