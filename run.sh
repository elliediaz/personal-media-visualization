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
#   install   - 의존성 설치
#   help      - 도움말 표시
#

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 기본 설정
HOST="${PMV_HOST:-0.0.0.0}"
PORT="${PMV_PORT:-8000}"
PYTHON="${PYTHON:-python3}"

# 로고 출력
print_logo() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "   Personal Media Visualization"
    echo "   오디오 분석 및 시각화 시스템"
    echo "=================================================="
    echo -e "${NC}"
}

# 정보 메시지
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# 경고 메시지
warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 오류 메시지
error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Python 확인
check_python() {
    if ! command -v $PYTHON &> /dev/null; then
        error "Python3가 설치되어 있지 않습니다."
    fi

    PYTHON_VERSION=$($PYTHON --version 2>&1 | cut -d' ' -f2)
    info "Python 버전: $PYTHON_VERSION"
}

# 가상환경 활성화 (존재하는 경우)
activate_venv() {
    if [ -d "venv" ]; then
        info "가상환경 활성화 중..."
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        info "가상환경 활성화 중..."
        source .venv/bin/activate
    fi
}

# 필수 디렉토리 생성
create_directories() {
    mkdir -p data/uploads data/cache output/renders output/exports temp logs
}

# 의존성 설치
install_deps() {
    info "의존성 설치 중..."
    $PYTHON -m pip install -r requirements.txt
    info "의존성 설치 완료"
}

# 개발 의존성 설치
install_dev_deps() {
    info "개발 의존성 설치 중..."
    $PYTHON -m pip install -r requirements-dev.txt
    info "개발 의존성 설치 완료"
}

# 서버 시작
start_server() {
    print_logo
    check_python
    activate_venv
    create_directories

    info "API 서버 시작 중..."
    info "주소: http://${HOST}:${PORT}"
    info "웹 인터페이스: http://${HOST}:${PORT}/web"
    info "API 문서: http://${HOST}:${PORT}/docs"
    echo ""
    info "종료하려면 Ctrl+C를 누르세요."
    echo ""

    $PYTHON run_api_server.py
}

# 개발 모드 서버 시작
start_dev_server() {
    print_logo
    check_python
    activate_venv
    create_directories

    info "개발 모드로 API 서버 시작 중..."
    info "주소: http://${HOST}:${PORT}"
    info "웹 인터페이스: http://${HOST}:${PORT}/web"
    info "API 문서: http://${HOST}:${PORT}/docs"
    echo ""
    info "종료하려면 Ctrl+C를 누르세요."
    echo ""

    $PYTHON -m uvicorn src.api.app:app --host $HOST --port $PORT --reload
}

# 테스트 실행
run_tests() {
    check_python
    activate_venv

    info "테스트 실행 중..."
    $PYTHON -m pytest tests/ -v
}

# 코드 품질 검사
run_lint() {
    check_python
    activate_venv

    info "코드 품질 검사 중..."

    if command -v black &> /dev/null; then
        info "Black 포매팅 검사..."
        $PYTHON -m black --check src tests
    fi

    if command -v ruff &> /dev/null; then
        info "Ruff 린팅..."
        $PYTHON -m ruff check src tests
    fi

    info "코드 품질 검사 완료"
}

# 도움말
show_help() {
    echo "Personal Media Visualization 실행 스크립트"
    echo ""
    echo "사용법: ./run.sh [명령어]"
    echo ""
    echo "명령어:"
    echo "  server    API 서버 시작 (기본값)"
    echo "  dev       개발 모드로 서버 시작 (자동 리로드)"
    echo "  test      테스트 실행"
    echo "  lint      코드 품질 검사"
    echo "  install   의존성 설치"
    echo "  help      이 도움말 표시"
    echo ""
    echo "환경 변수:"
    echo "  PMV_HOST  서버 호스트 (기본값: 0.0.0.0)"
    echo "  PMV_PORT  서버 포트 (기본값: 8000)"
    echo "  PYTHON    Python 실행 파일 (기본값: python3)"
    echo ""
    echo "예시:"
    echo "  ./run.sh                    # 서버 시작"
    echo "  ./run.sh dev                # 개발 모드"
    echo "  PMV_PORT=9000 ./run.sh      # 포트 9000에서 시작"
}

# 메인 실행
case "${1:-server}" in
    server)
        start_server
        ;;
    dev)
        start_dev_server
        ;;
    test)
        run_tests
        ;;
    lint)
        run_lint
        ;;
    install)
        install_deps
        ;;
    install-dev)
        install_dev_deps
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "알 수 없는 명령어: $1"
        show_help
        exit 1
        ;;
esac
