@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

:: ================================================================
::  Personal Media Visualization - GUI Launcher
::  군사용 메인프레임 스타일 오디오 시각화 시스템
:: ================================================================

title MAINFRAME AUDIO VISUALIZATION SYSTEM

:: 색상 설정 (녹색 텍스트, 검정 배경)
color 0A

:: 헤더 출력
echo.
echo  ================================================================
echo  ::                                                            ::
echo  ::    MAINFRAME AUDIO VISUALIZATION SYSTEM                    ::
echo  ::    Military-Grade Terminal Emulation v2.0                  ::
echo  ::                                                            ::
echo  ::    52 Visualization Styles Available                       ::
echo  ::                                                            ::
echo  ================================================================
echo.

:: Python 확인
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    where py >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo  [ERROR] Python이 설치되어 있지 않습니다.
        echo          https://www.python.org/downloads/ 에서 설치하세요.
        pause
        exit /b 1
    )
    set PYTHON=py
) else (
    set PYTHON=python
)

:: 인자 처리
set PHOSPHOR=green
set WIDTH=1024
set HEIGHT=768
set CRT=--crt
set HELP=0

:parse_args
if "%~1"=="" goto run
if /i "%~1"=="-h" set HELP=1 & shift & goto parse_args
if /i "%~1"=="--help" set HELP=1 & shift & goto parse_args
if /i "%~1"=="-p" set PHOSPHOR=%~2 & shift & shift & goto parse_args
if /i "%~1"=="--phosphor" set PHOSPHOR=%~2 & shift & shift & goto parse_args
if /i "%~1"=="-W" set WIDTH=%~2 & shift & shift & goto parse_args
if /i "%~1"=="--width" set WIDTH=%~2 & shift & shift & goto parse_args
if /i "%~1"=="-H" set HEIGHT=%~2 & shift & shift & goto parse_args
if /i "%~1"=="--height" set HEIGHT=%~2 & shift & shift & goto parse_args
if /i "%~1"=="--no-crt" set CRT=--no-crt & shift & goto parse_args
if /i "%~1"=="green" set PHOSPHOR=green & shift & goto parse_args
if /i "%~1"=="amber" set PHOSPHOR=amber & shift & goto parse_args
if /i "%~1"=="white" set PHOSPHOR=white & shift & goto parse_args
if /i "%~1"=="blue" set PHOSPHOR=blue & shift & goto parse_args
shift
goto parse_args

:run
if %HELP%==1 (
    echo  사용법: gui.bat [옵션] [색상]
    echo.
    echo  옵션:
    echo    -h, --help           도움말 표시
    echo    -p, --phosphor COLOR 인광체 색상 설정
    echo    -W, --width WIDTH    창 너비 설정 (기본값: 1024)
    echo    -H, --height HEIGHT  창 높이 설정 (기본값: 768)
    echo    --no-crt             CRT 효과 비활성화
    echo.
    echo  인광체 색상:
    echo    green   클래식 그린 (P1 인광체) - 기본값
    echo    amber   앰버 (P3 인광체)
    echo    white   화이트 (P4 인광체)
    echo    blue    군사용 블루
    echo.
    echo  단축키 (실행 중):
    echo    F1/F2       시각화 이전/다음 (52개 스타일)
    echo    F3          CRT 효과 토글
    echo    F4          인광체 색상 변경
    echo    F5          설정 화면 (오디오 입력 선택)
    echo    SPACE       재생/일시정지 (파일 모드)
    echo    ESC         종료
    echo.
    echo  예시:
    echo    gui.bat                    기본 실행 (그린)
    echo    gui.bat amber              앰버 인광체
    echo    gui.bat -p blue --no-crt   블루, CRT 효과 없이
    echo    gui.bat -W 1280 -H 960     큰 해상도
    echo.
    pause
    exit /b 0
)

:: 설정 출력
echo  ----------------------------------------------------------------
echo   설정 정보
echo  ----------------------------------------------------------------
echo   인광체 색상 : %PHOSPHOR%
echo   해상도      : %WIDTH% x %HEIGHT%
if "%CRT%"=="--no-crt" (
    echo   CRT 효과    : OFF
) else (
    echo   CRT 효과    : ON
)
echo  ----------------------------------------------------------------
echo.
echo   단축키:
echo     F1/F2   - 시각화 이전/다음 (52개 스타일)
echo     F3      - CRT 효과 토글
echo     F4      - 인광체 색상 변경
echo     F5      - 설정 (오디오 입력 선택)
echo     SPACE   - 재생/일시정지
echo     ESC     - 종료
echo.
echo  ----------------------------------------------------------------
echo   시스템 초기화 중...
echo  ----------------------------------------------------------------
echo.

:: GUI 실행
if "%CRT%"=="--no-crt" (
    %PYTHON% run_gui.py -p %PHOSPHOR% -W %WIDTH% -H %HEIGHT% --no-crt
) else (
    %PYTHON% run_gui.py -p %PHOSPHOR% -W %WIDTH% -H %HEIGHT%
)

:: 종료
echo.
echo  ----------------------------------------------------------------
echo   시스템 종료 완료
echo  ----------------------------------------------------------------
echo.

endlocal
