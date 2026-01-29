#!/bin/bash
#
# Personal Media Visualization 실행 스크립트
#
# 사용법:
#   ./run.sh [명령어]
#
# 명령어:
#   server    - API 서버 시작 (기본값)
#   dev       - 개발 모드로 서버 시작 (자동 리로드)
#   test      - 테스트 실행
#   lint      - 코드 품질 검사
#   format    - 코드 포매팅
#   check     - lint + type check
#   install   - 의존성 설치
#   build     - 프로젝트 빌드/패키징
#   clean     - 캐시 및 임시 파일 정리
#   docs      - 문서 생성
#   benchmark - 벤치마크 실행
#   coverage  - 커버리지 리포트 생성
#   info      - 시스템 정보 출력
#   help      - 도움말 표시
#

set -e

# ===== 색상 정의 =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ===== 프로젝트 설정 =====
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 기본 설정
HOST="${PMV_HOST:-0.0.0.0}"
PORT="${PMV_PORT:-8000}"
PYTHON="${PYTHON:-python3}"

# ===== 환경 감지 =====
IS_RASPBERRY_PI=false
IS_WSL=false
IS_MACOS=false
IS_LINUX=false

detect_environment() {
    # 라즈베리파이 감지
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        IS_RASPBERRY_PI=true
    fi

    # WSL 감지
    if grep -q Microsoft /proc/version 2>/dev/null || grep -q microsoft /proc/version 2>/dev/null; then
        IS_WSL=true
    fi

    # OS 감지
    case "$(uname -s)" in
        Darwin*) IS_MACOS=true ;;
        Linux*)  IS_LINUX=true ;;
    esac
}

detect_environment

# ===== 로고 및 메시지 함수 =====
print_logo() {
    echo -e "${CYAN}"
    echo "  ____  __  ____   __"
    echo " |  _ \\|  \\/  \\ \\ / /"
    echo " | |_) | |\\/| |\\ V / "
    echo " |  __/| |  | | | |  "
    echo " |_|   |_|  |_| |_|  "
    echo ""
    echo -e "${BOLD}Personal Media Visualization${NC}"
    echo -e "${BLUE}Audio Analysis & Visualization System${NC}"
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

progress() {
    echo -e "${CYAN}[...]${NC} $1"
}

# ===== 시스템 검사 =====
check_python() {
    if ! command -v $PYTHON &> /dev/null; then
        error "Python3가 설치되어 있지 않습니다."
    fi

    PYTHON_VERSION=$($PYTHON --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
        error "Python 3.10 이상이 필요합니다. 현재 버전: $PYTHON_VERSION"
    fi

    info "Python 버전: $PYTHON_VERSION"
}

check_dependencies() {
    local missing=()

    # 필수 패키지 확인
    $PYTHON -c "import fastapi" 2>/dev/null || missing+=("fastapi")
    $PYTHON -c "import uvicorn" 2>/dev/null || missing+=("uvicorn")
    $PYTHON -c "import librosa" 2>/dev/null || missing+=("librosa")

    if [ ${#missing[@]} -gt 0 ]; then
        warn "누락된 패키지: ${missing[*]}"
        warn "'./run.sh install'을 실행하여 의존성을 설치하세요."
        return 1
    fi

    return 0
}

# ===== 가상환경 =====
activate_venv() {
    if [ -d "venv" ]; then
        info "가상환경 활성화 중..."
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        info "가상환경 활성화 중..."
        source .venv/bin/activate
    fi
}

# ===== 디렉토리 관리 =====
create_directories() {
    mkdir -p data/uploads data/cache output/renders output/exports temp logs
}

# ===== 명령어 함수들 =====
install_deps() {
    check_python
    activate_venv

    info "의존성 설치 중..."
    $PYTHON -m pip install --upgrade pip
    $PYTHON -m pip install -r requirements.txt
    success "의존성 설치 완료"
}

install_dev_deps() {
    check_python
    activate_venv

    info "개발 의존성 설치 중..."
    $PYTHON -m pip install --upgrade pip
    $PYTHON -m pip install -r requirements.txt
    $PYTHON -m pip install -r requirements-dev.txt
    success "개발 의존성 설치 완료"
}

start_server() {
    print_logo
    check_python
    activate_venv
    create_directories

    if ! check_dependencies; then
        error "필수 의존성이 설치되지 않았습니다."
    fi

    if [ "$IS_RASPBERRY_PI" = true ]; then
        info "라즈베리파이 감지 - 최적화 모드 적용"
        export PMV_PERFORMANCE_MODE=low
    fi

    echo -e "${BOLD}API 서버 시작${NC}"
    echo ""
    info "주소: http://${HOST}:${PORT}"
    info "웹 인터페이스: http://${HOST}:${PORT}/web"
    info "API 문서: http://${HOST}:${PORT}/docs"
    echo ""
    info "종료하려면 Ctrl+C를 누르세요."
    echo ""

    $PYTHON run_api_server.py
}

start_dev_server() {
    print_logo
    check_python
    activate_venv
    create_directories

    if ! check_dependencies; then
        error "필수 의존성이 설치되지 않았습니다."
    fi

    echo -e "${BOLD}개발 모드 서버 시작${NC}"
    echo ""
    info "주소: http://${HOST}:${PORT}"
    info "웹 인터페이스: http://${HOST}:${PORT}/web"
    info "API 문서: http://${HOST}:${PORT}/docs"
    echo ""
    info "자동 리로드 활성화"
    info "종료하려면 Ctrl+C를 누르세요."
    echo ""

    $PYTHON -m uvicorn src.api.app:app --host $HOST --port $PORT --reload
}

run_tests() {
    check_python
    activate_venv

    info "테스트 실행 중..."
    echo ""

    if [ -n "$1" ]; then
        $PYTHON -m pytest "$@"
    else
        $PYTHON -m pytest tests/ -v --cov=src --cov-report=term-missing
    fi
}

run_lint() {
    check_python
    activate_venv

    info "코드 품질 검사 중..."
    echo ""

    local has_error=false

    if command -v ruff &> /dev/null || $PYTHON -m ruff --version &> /dev/null; then
        progress "Ruff 린팅 검사..."
        if $PYTHON -m ruff check src tests; then
            success "Ruff 검사 통과"
        else
            has_error=true
        fi
    else
        warn "Ruff가 설치되어 있지 않습니다."
    fi

    if command -v black &> /dev/null || $PYTHON -m black --version &> /dev/null; then
        progress "Black 포매팅 검사..."
        if $PYTHON -m black --check src tests; then
            success "Black 검사 통과"
        else
            has_error=true
        fi
    else
        warn "Black이 설치되어 있지 않습니다."
    fi

    if [ "$has_error" = true ]; then
        error "코드 품질 검사 실패"
    fi

    success "코드 품질 검사 완료"
}

run_format() {
    check_python
    activate_venv

    info "코드 포매팅 중..."
    echo ""

    if command -v black &> /dev/null || $PYTHON -m black --version &> /dev/null; then
        progress "Black으로 포매팅..."
        $PYTHON -m black src tests
        success "포매팅 완료"
    else
        warn "Black이 설치되어 있지 않습니다."
    fi

    if command -v ruff &> /dev/null || $PYTHON -m ruff --version &> /dev/null; then
        progress "Ruff로 자동 수정..."
        $PYTHON -m ruff check --fix src tests || true
        success "린트 수정 완료"
    fi
}

run_check() {
    check_python
    activate_venv

    info "전체 검사 실행 중..."
    echo ""

    run_lint

    if command -v mypy &> /dev/null || $PYTHON -m mypy --version &> /dev/null; then
        progress "MyPy 타입 검사..."
        if $PYTHON -m mypy src --ignore-missing-imports; then
            success "타입 검사 통과"
        else
            warn "타입 검사에서 경고/오류 발생"
        fi
    else
        warn "MyPy가 설치되어 있지 않습니다."
    fi

    success "전체 검사 완료"
}

run_build() {
    check_python
    activate_venv

    info "프로젝트 빌드 중..."
    echo ""

    # wheel 빌드
    if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
        progress "패키지 빌드..."
        $PYTHON -m pip install build
        $PYTHON -m build
        success "빌드 완료 - dist/ 디렉토리 확인"
    else
        warn "pyproject.toml 또는 setup.py를 찾을 수 없습니다."
    fi
}

run_clean() {
    info "정리 중..."
    echo ""

    progress "Python 캐시 삭제..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true

    progress "테스트/빌드 캐시 삭제..."
    rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov 2>/dev/null || true
    rm -rf build dist *.egg-info 2>/dev/null || true

    progress "임시 파일 삭제..."
    rm -rf temp/* 2>/dev/null || true

    success "정리 완료"
}

run_docs() {
    check_python
    activate_venv

    info "문서 생성 중..."
    echo ""

    if [ -d "docs" ]; then
        if command -v mkdocs &> /dev/null || $PYTHON -m mkdocs --version &> /dev/null; then
            progress "MkDocs로 문서 빌드..."
            $PYTHON -m mkdocs build
            success "문서 생성 완료 - site/ 디렉토리 확인"
        elif command -v sphinx-build &> /dev/null; then
            progress "Sphinx로 문서 빌드..."
            sphinx-build -b html docs docs/_build/html
            success "문서 생성 완료 - docs/_build/html/ 확인"
        else
            warn "문서 생성 도구(mkdocs/sphinx)가 설치되어 있지 않습니다."
        fi
    else
        warn "docs 디렉토리를 찾을 수 없습니다."
    fi
}

run_benchmark() {
    check_python
    activate_venv

    info "벤치마크 실행 중..."
    echo ""

    if [ -d "tests/benchmarks" ]; then
        $PYTHON -m pytest tests/benchmarks/ --benchmark-only -v
    else
        warn "벤치마크 디렉토리를 찾을 수 없습니다."
    fi
}

run_coverage() {
    check_python
    activate_venv

    info "커버리지 리포트 생성 중..."
    echo ""

    $PYTHON -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
    success "커버리지 리포트 생성 완료 - htmlcov/index.html 확인"
}

run_gui() {
    print_logo
    check_python
    activate_venv

    echo -e "${BOLD}메인프레임 GUI 시작${NC}"
    echo ""
    info "80~90년대 군사용 메인프레임 스타일 GUI"
    info "인광체: ${2:-green}"
    echo ""
    info "단축키:"
    info "  F1  - 파형 모드"
    info "  F2  - 오실로스코프 모드"
    info "  F3  - CRT 효과 토글"
    info "  F4  - 인광체 색상 변경"
    info "  ESC - 종료"
    echo ""

    $PYTHON run_gui.py "${@:2}"
}

show_info() {
    print_logo

    echo -e "${BOLD}시스템 정보${NC}"
    echo ""

    # Python 정보
    if command -v $PYTHON &> /dev/null; then
        echo -e "Python:        $($PYTHON --version 2>&1)"
        echo -e "Python 경로:   $(which $PYTHON)"
    fi

    # pip 정보
    if command -v pip &> /dev/null; then
        echo -e "pip:           $(pip --version 2>&1 | cut -d' ' -f2)"
    fi

    echo ""

    # 환경 정보
    echo -e "${BOLD}환경${NC}"
    echo -e "OS:            $(uname -s)"
    echo -e "아키텍처:      $(uname -m)"

    if [ "$IS_RASPBERRY_PI" = true ]; then
        echo -e "플랫폼:        Raspberry Pi"
        if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
            TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
            echo -e "CPU 온도:      $((TEMP/1000))°C"
        fi
    fi

    if [ "$IS_WSL" = true ]; then
        echo -e "플랫폼:        WSL (Windows Subsystem for Linux)"
    fi

    echo ""

    # 프로젝트 정보
    echo -e "${BOLD}프로젝트${NC}"
    echo -e "경로:          $SCRIPT_DIR"

    if [ -f "src/__init__.py" ]; then
        VERSION=$($PYTHON -c "from src import __version__; print(__version__)" 2>/dev/null || echo "N/A")
        echo -e "버전:          $VERSION"
    fi

    echo ""

    # 가상환경 정보
    echo -e "${BOLD}가상환경${NC}"
    if [ -d "venv" ]; then
        echo -e "위치:          venv/"
    elif [ -d ".venv" ]; then
        echo -e "위치:          .venv/"
    else
        echo -e "상태:          감지되지 않음"
    fi

    echo ""
}

show_help() {
    print_logo

    echo -e "${BOLD}사용법:${NC} ./run.sh [명령어] [옵션]"
    echo ""
    echo -e "${BOLD}서버 명령어:${NC}"
    echo "  server      API 서버 시작 (기본값)"
    echo "  dev         개발 모드로 서버 시작 (자동 리로드)"
    echo "  gui         메인프레임 스타일 GUI 실행"
    echo ""
    echo -e "${BOLD}개발 명령어:${NC}"
    echo "  test        테스트 실행"
    echo "  lint        코드 품질 검사 (ruff, black --check)"
    echo "  format      코드 포매팅 (black, ruff --fix)"
    echo "  check       전체 검사 (lint + type check)"
    echo "  coverage    커버리지 리포트 생성"
    echo "  benchmark   벤치마크 실행"
    echo ""
    echo -e "${BOLD}빌드 명령어:${NC}"
    echo "  install     의존성 설치"
    echo "  install-dev 개발 의존성 설치"
    echo "  build       프로젝트 빌드/패키징"
    echo "  clean       캐시 및 임시 파일 정리"
    echo "  docs        문서 생성"
    echo ""
    echo -e "${BOLD}유틸리티:${NC}"
    echo "  info        시스템 정보 출력"
    echo "  help        이 도움말 표시"
    echo ""
    echo -e "${BOLD}환경 변수:${NC}"
    echo "  PMV_HOST    서버 호스트 (기본값: 0.0.0.0)"
    echo "  PMV_PORT    서버 포트 (기본값: 8000)"
    echo "  PYTHON      Python 실행 파일 (기본값: python3)"
    echo ""
    echo -e "${BOLD}예시:${NC}"
    echo "  ./run.sh                    # 서버 시작"
    echo "  ./run.sh dev                # 개발 모드"
    echo "  ./run.sh test -k player     # 'player' 키워드 테스트만 실행"
    echo "  PMV_PORT=9000 ./run.sh      # 포트 9000에서 시작"
    echo ""
}

# ===== 메인 실행 =====
case "${1:-server}" in
    server)
        start_server
        ;;
    dev)
        start_dev_server
        ;;
    gui)
        shift
        run_gui "$@"
        ;;
    test)
        shift
        run_tests "$@"
        ;;
    lint)
        run_lint
        ;;
    format)
        run_format
        ;;
    check)
        run_check
        ;;
    install)
        install_deps
        ;;
    install-dev)
        install_dev_deps
        ;;
    build)
        run_build
        ;;
    clean)
        run_clean
        ;;
    docs)
        run_docs
        ;;
    benchmark)
        run_benchmark
        ;;
    coverage)
        run_coverage
        ;;
    info)
        show_info
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "알 수 없는 명령어: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
