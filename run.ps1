#Requires -Version 5.1
<#
.SYNOPSIS
    Personal Media Visualization 실행 스크립트 (PowerShell)

.DESCRIPTION
    오디오 분석 및 시각화 시스템의 PowerShell 실행 스크립트입니다.
    서버 시작, 테스트 실행, 코드 품질 검사 등을 수행합니다.

.PARAMETER Command
    실행할 명령어. 기본값: server

.EXAMPLE
    .\run.ps1
    API 서버를 시작합니다.

.EXAMPLE
    .\run.ps1 dev
    개발 모드로 서버를 시작합니다.

.EXAMPLE
    .\run.ps1 test -k player
    'player' 키워드가 포함된 테스트만 실행합니다.
#>

param(
    [Parameter(Position=0)]
    [ValidateSet('server', 'dev', 'gui', 'test', 'lint', 'format', 'check', 'install', 'install-dev', 'build', 'clean', 'docs', 'benchmark', 'coverage', 'info', 'help')]
    [string]$Command = 'server',

    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# 스크립트 설정
$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 환경 변수 기본값
$PMV_HOST = if ($env:PMV_HOST) { $env:PMV_HOST } else { '0.0.0.0' }
$PMV_PORT = if ($env:PMV_PORT) { $env:PMV_PORT } else { '8000' }
$PYTHON = if ($env:PYTHON) { $env:PYTHON } else { 'python' }

# ===== 색상 함수 =====
function Write-Color {
    param(
        [string]$Text,
        [ConsoleColor]$Color = 'White'
    )
    Write-Host $Text -ForegroundColor $Color -NoNewline
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

function Write-Err {
    param([string]$Message)
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Progress-Custom {
    param([string]$Message)
    Write-Host "[...] " -ForegroundColor Cyan -NoNewline
    Write-Host $Message
}

# ===== 로고 출력 =====
function Show-Logo {
    Write-Host ""
    Write-Host "  ____  __  ____   __" -ForegroundColor Cyan
    Write-Host " |  _ \|  \/  \ \ / /" -ForegroundColor Cyan
    Write-Host " | |_) | |\/| |\ V / " -ForegroundColor Cyan
    Write-Host " |  __/| |  | | | |  " -ForegroundColor Cyan
    Write-Host " |_|   |_|  |_| |_|  " -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Personal Media Visualization" -ForegroundColor White
    Write-Host "Audio Analysis & Visualization System" -ForegroundColor Blue
    Write-Host ""
    Write-Host ("=" * 50) -ForegroundColor Magenta
    Write-Host ""
}

# ===== Python 검사 =====
function Test-Python {
    try {
        $pythonVersion = & $PYTHON --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Python not found"
        }

        $versionMatch = $pythonVersion -match '(\d+)\.(\d+)\.(\d+)'
        if ($versionMatch) {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]

            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
                Write-Err "Python 3.10 이상이 필요합니다. 현재 버전: $pythonVersion"
                exit 1
            }
        }

        Write-Info "Python 버전: $pythonVersion"
        return $true
    }
    catch {
        Write-Err "Python이 설치되어 있지 않습니다."
        exit 1
    }
}

# ===== 가상환경 활성화 =====
function Enable-Venv {
    if (Test-Path "venv\Scripts\Activate.ps1") {
        Write-Info "가상환경 활성화 중..."
        & "venv\Scripts\Activate.ps1"
    }
    elseif (Test-Path ".venv\Scripts\Activate.ps1") {
        Write-Info "가상환경 활성화 중..."
        & ".venv\Scripts\Activate.ps1"
    }
}

# ===== 디렉토리 생성 =====
function New-Directories {
    $dirs = @(
        "data\uploads",
        "data\cache",
        "output\renders",
        "output\exports",
        "temp",
        "logs"
    )

    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
}

# ===== 서버 시작 =====
function Start-Server {
    Show-Logo
    Test-Python
    Enable-Venv
    New-Directories

    Write-Host "API 서버 시작" -ForegroundColor White
    Write-Host ""
    Write-Info "주소: http://${PMV_HOST}:${PMV_PORT}"
    Write-Info "웹 인터페이스: http://${PMV_HOST}:${PMV_PORT}/web"
    Write-Info "API 문서: http://${PMV_HOST}:${PMV_PORT}/docs"
    Write-Host ""
    Write-Info "종료하려면 Ctrl+C를 누르세요."
    Write-Host ""

    & $PYTHON run_api_server.py
}

# ===== 개발 서버 시작 =====
function Start-DevServer {
    Show-Logo
    Test-Python
    Enable-Venv
    New-Directories

    Write-Host "개발 모드 서버 시작" -ForegroundColor White
    Write-Host ""
    Write-Info "주소: http://${PMV_HOST}:${PMV_PORT}"
    Write-Info "웹 인터페이스: http://${PMV_HOST}:${PMV_PORT}/web"
    Write-Info "API 문서: http://${PMV_HOST}:${PMV_PORT}/docs"
    Write-Host ""
    Write-Info "자동 리로드 활성화"
    Write-Info "종료하려면 Ctrl+C를 누르세요."
    Write-Host ""

    & $PYTHON -m uvicorn src.api.app:app --host $PMV_HOST --port $PMV_PORT --reload
}

# ===== 메인프레임 GUI 시작 =====
function Start-Gui {
    Show-Logo
    Test-Python
    Enable-Venv

    Write-Host "메인프레임 GUI 시작" -ForegroundColor White
    Write-Host ""
    Write-Info "80~90년대 군사용 메인프레임 스타일 GUI"
    Write-Host ""
    Write-Info "단축키:"
    Write-Info "  F1  - 파형 모드"
    Write-Info "  F2  - 오실로스코프 모드"
    Write-Info "  F3  - CRT 효과 토글"
    Write-Info "  F4  - 인광체 색상 변경"
    Write-Info "  ESC - 종료"
    Write-Host ""

    if ($Arguments) {
        & $PYTHON run_gui.py $Arguments
    }
    else {
        & $PYTHON run_gui.py
    }
}

# ===== 테스트 실행 =====
function Invoke-Tests {
    Test-Python
    Enable-Venv

    Write-Info "테스트 실행 중..."
    Write-Host ""

    if ($Arguments) {
        & $PYTHON -m pytest $Arguments
    }
    else {
        & $PYTHON -m pytest tests/ -v --cov=src --cov-report=term-missing
    }
}

# ===== 린트 검사 =====
function Invoke-Lint {
    Test-Python
    Enable-Venv

    Write-Info "코드 품질 검사 중..."
    Write-Host ""

    Write-Progress-Custom "Ruff 린팅 검사..."
    & $PYTHON -m ruff check src tests
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Ruff 검사 통과"
    }
    else {
        Write-Warn "Ruff 검사에서 문제 발견"
    }

    Write-Progress-Custom "Black 포매팅 검사..."
    & $PYTHON -m black --check src tests
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Black 검사 통과"
    }
    else {
        Write-Warn "Black 검사에서 문제 발견"
    }

    Write-Host ""
    Write-Info "코드 품질 검사 완료"
}

# ===== 코드 포매팅 =====
function Invoke-Format {
    Test-Python
    Enable-Venv

    Write-Info "코드 포매팅 중..."
    Write-Host ""

    Write-Progress-Custom "Black으로 포매팅..."
    & $PYTHON -m black src tests
    Write-Success "포매팅 완료"

    Write-Progress-Custom "Ruff로 자동 수정..."
    & $PYTHON -m ruff check --fix src tests 2>$null
    Write-Success "린트 수정 완료"
}

# ===== 전체 검사 =====
function Invoke-Check {
    Test-Python
    Enable-Venv

    Write-Info "전체 검사 실행 중..."
    Write-Host ""

    Invoke-Lint

    Write-Progress-Custom "MyPy 타입 검사..."
    & $PYTHON -m mypy src --ignore-missing-imports
    if ($LASTEXITCODE -eq 0) {
        Write-Success "타입 검사 통과"
    }
    else {
        Write-Warn "타입 검사에서 경고/오류 발생"
    }

    Write-Host ""
    Write-Success "전체 검사 완료"
}

# ===== 의존성 설치 =====
function Install-Dependencies {
    Test-Python
    Enable-Venv

    Write-Info "의존성 설치 중..."
    & $PYTHON -m pip install --upgrade pip
    & $PYTHON -m pip install -r requirements.txt
    Write-Success "의존성 설치 완료"
}

# ===== 개발 의존성 설치 =====
function Install-DevDependencies {
    Test-Python
    Enable-Venv

    Write-Info "개발 의존성 설치 중..."
    & $PYTHON -m pip install --upgrade pip
    & $PYTHON -m pip install -r requirements.txt
    & $PYTHON -m pip install -r requirements-dev.txt
    Write-Success "개발 의존성 설치 완료"
}

# ===== 빌드 =====
function Invoke-Build {
    Test-Python
    Enable-Venv

    Write-Info "프로젝트 빌드 중..."
    Write-Host ""

    if ((Test-Path "pyproject.toml") -or (Test-Path "setup.py")) {
        Write-Progress-Custom "패키지 빌드..."
        & $PYTHON -m pip install build
        & $PYTHON -m build
        Write-Success "빌드 완료 - dist\ 디렉토리 확인"
    }
    else {
        Write-Warn "pyproject.toml 또는 setup.py를 찾을 수 없습니다."
    }
}

# ===== 정리 =====
function Invoke-Clean {
    Write-Info "정리 중..."
    Write-Host ""

    Write-Progress-Custom "Python 캐시 삭제..."
    Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -File -Filter "*.pyo" | Remove-Item -Force -ErrorAction SilentlyContinue

    Write-Progress-Custom "테스트/빌드 캐시 삭제..."
    $cacheDirs = @(".pytest_cache", ".mypy_cache", ".ruff_cache", "htmlcov", "build", "dist")
    foreach ($dir in $cacheDirs) {
        if (Test-Path $dir) {
            Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    if (Test-Path ".coverage") {
        Remove-Item -Path ".coverage" -Force -ErrorAction SilentlyContinue
    }
    Get-ChildItem -Path . -Directory -Filter "*.egg-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    Write-Progress-Custom "임시 파일 삭제..."
    if (Test-Path "temp") {
        Get-ChildItem -Path "temp" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-Success "정리 완료"
}

# ===== 문서 생성 =====
function Invoke-Docs {
    Test-Python
    Enable-Venv

    Write-Info "문서 생성 중..."
    Write-Host ""

    if (Test-Path "docs") {
        try {
            & $PYTHON -m mkdocs build
            Write-Success "문서 생성 완료 - site\ 디렉토리 확인"
        }
        catch {
            Write-Warn "MkDocs를 찾을 수 없습니다."
        }
    }
    else {
        Write-Warn "docs 디렉토리를 찾을 수 없습니다."
    }
}

# ===== 벤치마크 =====
function Invoke-Benchmark {
    Test-Python
    Enable-Venv

    Write-Info "벤치마크 실행 중..."
    Write-Host ""

    if (Test-Path "tests\benchmarks") {
        & $PYTHON -m pytest tests\benchmarks\ --benchmark-only -v
    }
    else {
        Write-Warn "벤치마크 디렉토리를 찾을 수 없습니다."
    }
}

# ===== 커버리지 =====
function Invoke-Coverage {
    Test-Python
    Enable-Venv

    Write-Info "커버리지 리포트 생성 중..."
    Write-Host ""

    & $PYTHON -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
    Write-Success "커버리지 리포트 생성 완료 - htmlcov\index.html 확인"
}

# ===== 시스템 정보 =====
function Show-Info {
    Show-Logo

    Write-Host "시스템 정보" -ForegroundColor White
    Write-Host ""

    # Python 정보
    try {
        $pythonVersion = & $PYTHON --version 2>&1
        $pythonPath = (Get-Command $PYTHON -ErrorAction SilentlyContinue).Source
        Write-Host "Python:        $pythonVersion"
        Write-Host "Python 경로:   $pythonPath"
    }
    catch {
        Write-Host "Python:        설치되지 않음"
    }
    Write-Host ""

    # 환경 정보
    Write-Host "환경" -ForegroundColor White
    Write-Host "OS:            Windows"
    Write-Host "버전:          $([System.Environment]::OSVersion.Version)"
    Write-Host "PowerShell:    $($PSVersionTable.PSVersion)"
    Write-Host ""

    # 프로젝트 정보
    Write-Host "프로젝트" -ForegroundColor White
    Write-Host "경로:          $ScriptDir"

    if (Test-Path "src\__init__.py") {
        try {
            $version = & $PYTHON -c "from src import __version__; print(__version__)" 2>$null
            Write-Host "버전:          $version"
        }
        catch {}
    }
    Write-Host ""

    # 가상환경 정보
    Write-Host "가상환경" -ForegroundColor White
    if (Test-Path "venv") {
        Write-Host "위치:          venv\"
    }
    elseif (Test-Path ".venv") {
        Write-Host "위치:          .venv\"
    }
    else {
        Write-Host "상태:          감지되지 않음"
    }
    Write-Host ""
}

# ===== 도움말 =====
function Show-Help {
    Show-Logo

    Write-Host "사용법: " -NoNewline
    Write-Host ".\run.ps1 [명령어] [옵션]" -ForegroundColor White
    Write-Host ""

    Write-Host "서버 명령어:" -ForegroundColor White
    Write-Host "  server      API 서버 시작 (기본값)"
    Write-Host "  dev         개발 모드로 서버 시작 (자동 리로드)"
    Write-Host "  gui         메인프레임 스타일 GUI 실행"
    Write-Host ""

    Write-Host "개발 명령어:" -ForegroundColor White
    Write-Host "  test        테스트 실행"
    Write-Host "  lint        코드 품질 검사 (ruff, black --check)"
    Write-Host "  format      코드 포매팅 (black, ruff --fix)"
    Write-Host "  check       전체 검사 (lint + type check)"
    Write-Host "  coverage    커버리지 리포트 생성"
    Write-Host "  benchmark   벤치마크 실행"
    Write-Host ""

    Write-Host "빌드 명령어:" -ForegroundColor White
    Write-Host "  install     의존성 설치"
    Write-Host "  install-dev 개발 의존성 설치"
    Write-Host "  build       프로젝트 빌드/패키징"
    Write-Host "  clean       캐시 및 임시 파일 정리"
    Write-Host "  docs        문서 생성"
    Write-Host ""

    Write-Host "유틸리티:" -ForegroundColor White
    Write-Host "  info        시스템 정보 출력"
    Write-Host "  help        이 도움말 표시"
    Write-Host ""

    Write-Host "환경 변수:" -ForegroundColor White
    Write-Host "  PMV_HOST    서버 호스트 (기본값: 0.0.0.0)"
    Write-Host "  PMV_PORT    서버 포트 (기본값: 8000)"
    Write-Host "  PYTHON      Python 실행 파일 (기본값: python)"
    Write-Host ""

    Write-Host "예시:" -ForegroundColor White
    Write-Host "  .\run.ps1                         # 서버 시작"
    Write-Host "  .\run.ps1 dev                     # 개발 모드"
    Write-Host "  .\run.ps1 test -k player          # 'player' 키워드 테스트만 실행"
    Write-Host '  $env:PMV_PORT=9000; .\run.ps1     # 포트 9000에서 시작'
    Write-Host ""
}

# ===== 메인 실행 =====
switch ($Command) {
    'server'      { Start-Server }
    'dev'         { Start-DevServer }
    'gui'         { Start-Gui }
    'test'        { Invoke-Tests }
    'lint'        { Invoke-Lint }
    'format'      { Invoke-Format }
    'check'       { Invoke-Check }
    'install'     { Install-Dependencies }
    'install-dev' { Install-DevDependencies }
    'build'       { Invoke-Build }
    'clean'       { Invoke-Clean }
    'docs'        { Invoke-Docs }
    'benchmark'   { Invoke-Benchmark }
    'coverage'    { Invoke-Coverage }
    'info'        { Show-Info }
    'help'        { Show-Help }
    default       { Show-Help }
}
