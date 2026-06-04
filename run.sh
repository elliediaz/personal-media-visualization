#!/usr/bin/env bash
#
# Personal Media Visualization — 통합 실행 스크립트 (./run.sh)
#
# 사용법:
#   ./run.sh [명령어] [옵션]
#
# 명령어:
#   server      - API 서버 시작 (포그라운드, 기본값)
#   dev         - 개발 모드로 서버 시작 (자동 리로드)
#   serve       - server 별칭 (--tunnel / --open 옵션 지원)
#   start       - 백그라운드 데몬으로 서버 시작
#   stop        - 데몬 서버 종료
#   restart     - 데몬 재시작
#   status      - 데몬 상태 확인
#   logs        - 데몬 로그 follow
#   gui         - 메인프레임 스타일 GUI 실행
#   test        - 테스트 실행
#   lint        - 코드 품질 검사
#   format      - 코드 포매팅
#   check       - lint + type check
#   doctor      - 환경/의존성 점검
#   install     - 의존성 설치
#   install-dev - 개발 의존성 설치
#   build       - 프로젝트 빌드/패키징
#   clean       - 캐시 및 임시 파일 정리
#   docs        - 문서 생성
#   benchmark   - 벤치마크 실행
#   coverage    - 커버리지 리포트 생성
#   info        - 시스템 정보 출력
#   version     - 버전 출력
#   help        - 도움말 표시
#
# 옵션 (serve/server/dev/start):
#   --port N                              서버 포트 (기본값: 8000)
#   --host H                              바인드 호스트 (기본값: 0.0.0.0)
#   --tunnel [cloudflared|localhost.run]  외부 노출 터널
#   --open                                기본 브라우저로 /web 자동 오픈
#

set -euo pipefail

# ===== 프로젝트 설정 =====
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 기본 설정 (환경변수로 오버라이드 가능)
HOST="${PMV_HOST:-0.0.0.0}"
PORT="${PMV_PORT:-8000}"
VENV_DIR="$SCRIPT_DIR/.venv"
PID_FILE="$SCRIPT_DIR/.run/app.pid"
LOG_FILE="$SCRIPT_DIR/.run/app.log"

# 시스템 python: 3.10 기본, 3.11 가용, 3.12 없음 (Jetson aarch64)
PYTHON_BIN="${PYTHON:-python3.11}"
MIN_PY_MINOR=10

VERSION="$(git -C "$SCRIPT_DIR" describe --tags --always 2>/dev/null || echo 0.1.0)"

# ===== 색상 정의 (TTY 감지) =====
if [[ -t 1 ]]; then
    RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'
    BLUE=$'\033[0;34m'; MAGENTA=$'\033[0;35m'; CYAN=$'\033[0;36m'
    BOLD=$'\033[1m'; NC=$'\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; BLUE=''; MAGENTA=''; CYAN=''; BOLD=''; NC=''
fi

# ===== 환경 감지 =====
IS_RASPBERRY_PI=false
IS_JETSON=false
IS_WSL=false
IS_MACOS=false
IS_LINUX=false

detect_environment() {
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        IS_RASPBERRY_PI=true
    fi
    if [ -f /proc/device-tree/model ] && grep -qi "jetson\|tegra\|nvidia" /proc/device-tree/model 2>/dev/null; then
        IS_JETSON=true
    fi
    if grep -qi microsoft /proc/version 2>/dev/null; then
        IS_WSL=true
    fi
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
    echo -e "${BOLD}Personal Media Visualization${NC} ${CYAN}v${VERSION}${NC}"
    echo -e "${BLUE}Audio Analysis & Visualization System${NC}"
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

info()     { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()     { echo -e "${YELLOW}[WARN]${NC} $1" >&2; }
success()  { echo -e "${GREEN}[OK]${NC} $1"; }
progress() { echo -e "${CYAN}[...]${NC} $1"; }
error()    { echo -e "${RED}[ERROR]${NC} $1" >&2; exit 1; }

# ===== Python / venv 해석 =====
_resolve_python() {
    if ! command -v "$PYTHON_BIN" &>/dev/null; then
        for c in python3.11 python3.10 python3; do
            command -v "$c" &>/dev/null && { PYTHON_BIN="$c"; break; }
        done
    fi
    command -v "$PYTHON_BIN" &>/dev/null || error "Python이 설치되어 있지 않습니다 (python3.11/3.10 필요)."

    local m
    m=$("$PYTHON_BIN" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo 0)
    if (( m < MIN_PY_MINOR )); then
        error "Python 3.${MIN_PY_MINOR} 이상이 필요합니다. 현재: $("$PYTHON_BIN" --version 2>&1)"
    fi
}

# venv 안의 python 경로
_venv_py() { echo "$VENV_DIR/bin/python"; }

# venv 자동 생성 + 의존성 설치 (스탬프 기반 캐시)
# $1 = "dev" 이면 개발 의존성까지 설치
_ensure_venv() {
    local want_dev="${1:-}"
    _resolve_python

    if [ ! -d "$VENV_DIR" ]; then
        info "가상환경 생성 중... ($PYTHON_BIN -> $VENV_DIR)"
        "$PYTHON_BIN" -m venv "$VENV_DIR" || error "가상환경 생성 실패"
    fi

    # 기존 .venv 가 깨졌는지(파이썬 실행 불가) 확인 — 자동 삭제하지 않고 안내만
    if [ ! -x "$VENV_DIR/bin/python" ]; then
        error "가상환경이 손상되었습니다. '$VENV_DIR'를 삭제 후 다시 시도하세요: rm -rf '$VENV_DIR' && ./run.sh install"
    fi

    local stamp="$VENV_DIR/.installed"
    local dev_stamp="$VENV_DIR/.installed-dev"
    local need=0
    [ -f "$stamp" ] || need=1
    for f in pyproject.toml requirements.txt requirements-dev.txt setup.py setup.cfg; do
        [ -f "$f" ] && [ "$f" -nt "$stamp" ] && need=1
    done
    if [ "$want_dev" = "dev" ] && [ ! -f "$dev_stamp" ]; then
        need=1
    fi

    if (( need )); then
        info "의존성 설치/갱신 중... (시간이 걸릴 수 있습니다)"
        "$VENV_DIR/bin/pip" install -q --upgrade pip
        if [ -f requirements.txt ]; then
            "$VENV_DIR/bin/pip" install -q -r requirements.txt || error "requirements.txt 설치 실패"
        fi
        # editable 설치 (CLI 진입점 pmv 등록)
        if [ -f pyproject.toml ] || [ -f setup.py ]; then
            "$VENV_DIR/bin/pip" install -q -e . 2>/dev/null || true
        fi
        if [ "$want_dev" = "dev" ] && [ -f requirements-dev.txt ]; then
            "$VENV_DIR/bin/pip" install -q -r requirements-dev.txt || warn "개발 의존성 일부 설치 실패"
            touch "$dev_stamp"
        fi
        touch "$stamp"
        success "의존성 준비 완료"
    fi
}

# venv python 으로 실행 (venv 미존재 시 시스템 python fallback — 가벼운 작업용)
PY() {
    if [ -x "$VENV_DIR/bin/python" ]; then
        "$VENV_DIR/bin/python" "$@"
    else
        "$PYTHON_BIN" "$@"
    fi
}

# ===== 디렉토리 관리 =====
create_directories() {
    mkdir -p data/uploads data/cache output/renders output/exports temp logs
}

# ===== 옵션 파서 (serve/server/dev/start 공용) =====
TUNNEL_PROVIDER=""
OPEN_BROWSER=false
RELOAD=false
PASSTHRU_ARGS=()

parse_serve_opts() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --port)   PORT="$2"; shift 2 ;;
            --port=*) PORT="${1#*=}"; shift ;;
            --host)   HOST="$2"; shift 2 ;;
            --host=*) HOST="${1#*=}"; shift ;;
            --tunnel)
                if [ $# -ge 2 ] && [[ "$2" != --* ]]; then TUNNEL_PROVIDER="$2"; shift 2
                else TUNNEL_PROVIDER="cloudflared"; shift; fi ;;
            --tunnel=*) TUNNEL_PROVIDER="${1#*=}"; shift ;;
            --open)   OPEN_BROWSER=true; shift ;;
            --reload) RELOAD=true; shift ;;
            *) PASSTHRU_ARGS+=("$1"); shift ;;
        esac
    done
}

# ===== 터널링 (S4: cloudflared + localhost.run) =====
TUNNEL_PID=""
TUNNEL_LOG=""
cleanup_tunnel() {
    if [ -n "$TUNNEL_PID" ] && kill -0 "$TUNNEL_PID" 2>/dev/null; then
        kill "$TUNNEL_PID" 2>/dev/null || true
        sleep 1
        kill -9 "$TUNNEL_PID" 2>/dev/null || true
    fi
    [ -n "$TUNNEL_LOG" ] && [ -f "$TUNNEL_LOG" ] && rm -f "$TUNNEL_LOG"
}

gen_token() {
    if command -v openssl &>/dev/null; then openssl rand -hex 16
    else head -c16 /dev/urandom | od -An -tx1 | tr -d ' \n'; fi
}

start_tunnel() {  # $1=provider $2=port
    local provider="$1" port="$2" url=""
    TUNNEL_LOG="$(mktemp -t pmv-tunnel.XXXXXX.log)"
    case "$provider" in
        cloudflared|cf)
            if ! command -v cloudflared &>/dev/null; then
                warn "cloudflared 미설치 — 설치: https://github.com/cloudflare/cloudflared/releases (linux-arm64)"
                warn "또는 --tunnel localhost.run 사용 (ssh 기반)"
                return 1
            fi
            nohup cloudflared tunnel --no-autoupdate --url "http://localhost:${port}" >"$TUNNEL_LOG" 2>&1 &
            TUNNEL_PID=$!
            for _ in $(seq 1 40); do
                kill -0 "$TUNNEL_PID" 2>/dev/null || { warn "cloudflared 종료됨"; tail -10 "$TUNNEL_LOG" >&2; return 1; }
                url=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | head -1)
                [ -n "$url" ] && break
                sleep 0.5
            done ;;
        localhost.run|lhr)
            command -v ssh &>/dev/null || { warn "ssh가 필요합니다."; return 1; }
            nohup ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
                -NTR "80:localhost:${port}" nokey@localhost.run >"$TUNNEL_LOG" 2>&1 &
            TUNNEL_PID=$!
            for _ in $(seq 1 60); do
                kill -0 "$TUNNEL_PID" 2>/dev/null || { warn "ssh 터널 종료됨"; tail -10 "$TUNNEL_LOG" >&2; return 1; }
                url=$(grep -oE 'https://[a-zA-Z0-9-]+\.(lhr\.life|lhrtunnel\.link)' "$TUNNEL_LOG" 2>/dev/null | head -1)
                [ -n "$url" ] && break
                sleep 0.5
            done ;;
        *)
            warn "알 수 없는 터널 공급자: $provider (cloudflared|localhost.run)"
            return 1 ;;
    esac
    if [ -z "$url" ]; then
        warn "터널 URL 획득 실패"
        tail -10 "$TUNNEL_LOG" >&2
        return 1
    fi
    echo
    printf '%s┌── 터널 활성화 ─────────────────────────┐%s\n' "$CYAN" "$NC"
    printf '  공개 URL : %s%s/web%s\n' "$GREEN" "$url" "$NC"
    printf '  API 문서 : %s%s/docs%s\n' "$GREEN" "$url" "$NC"
    printf '  로컬 포트: %s | 로그: %s\n' "$port" "$TUNNEL_LOG"
    printf '%s└────────────────────────────────────────┘%s\n' "$CYAN" "$NC"
    echo
}

# ===== 브라우저 자동 오픈 (S5) =====
open_browser() {  # $1=url
    local url="$1"
    ( sleep 2
      if command -v xdg-open &>/dev/null; then xdg-open "$url"
      elif command -v open &>/dev/null; then open "$url"
      elif [ -n "${BROWSER:-}" ]; then "$BROWSER" "$url"; fi
    ) >/dev/null 2>&1 &
}

# ===== 시스템 검사 =====
check_dependencies() {
    local missing=()
    PY -c "import fastapi" 2>/dev/null || missing+=("fastapi")
    PY -c "import uvicorn" 2>/dev/null || missing+=("uvicorn")
    PY -c "import librosa" 2>/dev/null || missing+=("librosa")
    if [ ${#missing[@]} -gt 0 ]; then
        warn "누락된 패키지: ${missing[*]}"
        warn "'./run.sh install'을 실행하여 의존성을 설치하세요."
        return 1
    fi
    return 0
}

# ===== 명령어 함수들 =====
install_deps() {
    info "의존성 설치 중..."
    _ensure_venv
    success "의존성 설치 완료 (venv: $VENV_DIR)"
}

install_dev_deps() {
    info "개발 의존성 설치 중..."
    _ensure_venv dev
    success "개발 의존성 설치 완료 (venv: $VENV_DIR)"
}

_print_urls() {
    info "주소: http://${HOST}:${PORT}"
    info "웹 인터페이스: http://${HOST}:${PORT}/web"
    info "API 문서: http://${HOST}:${PORT}/docs"
}

# 브라우저 오픈/터널용 접속 URL (0.0.0.0 -> localhost)
_local_url() {
    local h="$HOST"
    [ "$h" = "0.0.0.0" ] && h="localhost"
    echo "http://${h}:${PORT}/web"
}

start_server() {
    parse_serve_opts "$@"
    print_logo
    _ensure_venv
    create_directories

    if ! check_dependencies; then
        error "필수 의존성이 설치되지 않았습니다."
    fi

    if [ "$IS_RASPBERRY_PI" = true ] || [ "$IS_JETSON" = true ]; then
        info "저전력 보드 감지 - 최적화 모드 적용"
        export PMV_PERFORMANCE_MODE=low
    fi

    echo -e "${BOLD}API 서버 시작${NC}"
    echo ""
    _print_urls
    echo ""

    # 터널 (옵션)
    if [ -n "$TUNNEL_PROVIDER" ]; then
        trap cleanup_tunnel EXIT INT TERM
        start_tunnel "$TUNNEL_PROVIDER" "$PORT" || warn "터널 시작 실패 — 로컬에서만 접속 가능"
    fi
    # 브라우저 오픈 (옵션)
    if [ "$OPEN_BROWSER" = true ]; then
        open_browser "$(_local_url)"
    fi

    info "종료하려면 Ctrl+C를 누르세요."
    echo ""

    export PMV_HOST="$HOST" PMV_PORT="$PORT"
    PY run_api_server.py
}

start_dev_server() {
    RELOAD=true
    parse_serve_opts "$@"
    print_logo
    _ensure_venv
    create_directories

    if ! check_dependencies; then
        error "필수 의존성이 설치되지 않았습니다."
    fi

    echo -e "${BOLD}개발 모드 서버 시작${NC}"
    echo ""
    _print_urls
    echo ""
    info "자동 리로드 활성화"

    if [ -n "$TUNNEL_PROVIDER" ]; then
        trap cleanup_tunnel EXIT INT TERM
        start_tunnel "$TUNNEL_PROVIDER" "$PORT" || warn "터널 시작 실패 — 로컬에서만 접속 가능"
    fi
    if [ "$OPEN_BROWSER" = true ]; then
        open_browser "$(_local_url)"
    fi

    info "종료하려면 Ctrl+C를 누르세요."
    echo ""

    PY -m uvicorn src.api.app:app --host "$HOST" --port "$PORT" --reload
}

# ===== 데몬 모드 (백그라운드, PID 파일) =====
_is_running() { [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null; }

daemon_start() {
    parse_serve_opts "$@"
    if _is_running; then
        warn "이미 실행 중 (PID $(cat "$PID_FILE"))"
        return 0
    fi
    _ensure_venv
    create_directories
    mkdir -p "$(dirname "$PID_FILE")"

    info "백그라운드 서버 시작 중..."
    PMV_HOST="$HOST" PMV_PORT="$PORT" nohup "$(_venv_py)" run_api_server.py >"$LOG_FILE" 2>&1 &
    echo $! >"$PID_FILE"
    sleep 1
    if _is_running; then
        success "시작됨 (PID $(cat "$PID_FILE"))"
        _print_urls
        info "로그: $LOG_FILE  ('./run.sh logs'로 확인)"
        if [ -n "$TUNNEL_PROVIDER" ]; then
            warn "데몬 모드에서는 --tunnel이 포그라운드 유지가 필요합니다. './run.sh serve --tunnel ...'을 사용하세요."
        fi
    else
        error "서버 시작 실패 — 로그 확인: $LOG_FILE"
    fi
}

daemon_stop() {
    if ! _is_running; then
        warn "실행 중이 아닙니다."
        rm -f "$PID_FILE"
        return 0
    fi
    local pid; pid="$(cat "$PID_FILE")"
    info "종료 중 (PID $pid)..."
    kill "$pid" 2>/dev/null || true
    sleep 1
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    success "종료됨"
}

daemon_status() {
    if _is_running; then
        success "실행 중 (PID $(cat "$PID_FILE"))"
        _print_urls
    else
        warn "중지 상태"
    fi
}

daemon_restart() {
    daemon_stop
    sleep 1
    daemon_start "$@"
}

daemon_logs() {
    [ -f "$LOG_FILE" ] || error "로그 파일이 없습니다: $LOG_FILE"
    tail -f "$LOG_FILE"
}

run_tests() {
    info "테스트 실행 중..."
    _ensure_venv dev
    echo ""
    if [ $# -gt 0 ]; then
        PY -m pytest "$@"
    else
        PY -m pytest tests/ -v --cov=src --cov-report=term-missing
    fi
}

run_lint() {
    info "코드 품질 검사 중..."
    _ensure_venv dev
    echo ""
    local has_error=false

    if PY -m ruff --version &>/dev/null; then
        progress "Ruff 린팅 검사..."
        if PY -m ruff check src tests; then success "Ruff 검사 통과"; else has_error=true; fi
    else
        warn "Ruff가 설치되어 있지 않습니다."
    fi

    if PY -m black --version &>/dev/null; then
        progress "Black 포매팅 검사..."
        if PY -m black --check src tests; then success "Black 검사 통과"; else has_error=true; fi
    else
        warn "Black이 설치되어 있지 않습니다."
    fi

    if [ "$has_error" = true ]; then
        error "코드 품질 검사 실패"
    fi
    success "코드 품질 검사 완료"
}

run_format() {
    info "코드 포매팅 중..."
    _ensure_venv dev
    echo ""
    if PY -m black --version &>/dev/null; then
        progress "Black으로 포매팅..."
        PY -m black src tests
        success "포매팅 완료"
    else
        warn "Black이 설치되어 있지 않습니다."
    fi
    if PY -m ruff --version &>/dev/null; then
        progress "Ruff로 자동 수정..."
        PY -m ruff check --fix src tests || true
        success "린트 수정 완료"
    fi
}

run_check() {
    info "전체 검사 실행 중..."
    _ensure_venv dev
    echo ""
    run_lint
    if PY -m mypy --version &>/dev/null; then
        progress "MyPy 타입 검사..."
        if PY -m mypy src --ignore-missing-imports; then success "타입 검사 통과"; else warn "타입 검사에서 경고/오류 발생"; fi
    else
        warn "MyPy가 설치되어 있지 않습니다."
    fi
    success "전체 검사 완료"
}

# 환경/의존성 점검 (가벼움 - 핵심 패키지 import 여부만 확인)
run_doctor() {
    print_logo
    echo -e "${BOLD}환경/의존성 점검${NC}"
    echo ""
    _resolve_python
    info "시스템 Python: $("$PYTHON_BIN" --version 2>&1) ($PYTHON_BIN)"
    if [ -x "$VENV_DIR/bin/python" ]; then
        info "venv Python : $("$VENV_DIR/bin/python" --version 2>&1)"
        info "venv 상태   : $VENV_DIR $([ -f "$VENV_DIR/.installed" ] && echo '(설치됨)' || echo '(미설치)')"
    else
        warn "venv 미생성 — './run.sh install' 실행 필요"
    fi
    info "아키텍처    : $(uname -m)"
    echo ""
    if [ -x "$VENV_DIR/bin/python" ]; then
        progress "핵심 패키지 import 점검..."
        "$VENV_DIR/bin/python" - <<'PYCHK' || warn "일부 패키지 누락 — './run.sh install' 실행"
import importlib.util, sys
mods = ["fastapi", "uvicorn", "librosa", "numpy", "pydantic"]
miss = [m for m in mods if importlib.util.find_spec(m) is None]
if miss:
    print("  누락:", ", ".join(miss)); sys.exit(1)
print("  핵심 패키지 OK")
PYCHK
    else
        warn "패키지 점검 건너뜀 (venv 없음)"
    fi
    echo ""
    success "점검 완료"
}

run_build() {
    info "프로젝트 빌드 중..."
    _ensure_venv dev
    echo ""
    if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
        progress "패키지 빌드..."
        PY -m pip install -q build
        PY -m build
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
    rm -rf build dist ./*.egg-info 2>/dev/null || true
    progress "임시 파일 삭제..."
    rm -rf temp/* 2>/dev/null || true
    success "정리 완료 (.venv 는 보존됨)"
}

run_docs() {
    info "문서 생성 중..."
    _ensure_venv dev
    echo ""
    if [ -d "docs" ]; then
        if PY -m mkdocs --version &>/dev/null; then
            progress "MkDocs로 문서 빌드..."
            PY -m mkdocs build
            success "문서 생성 완료 - site/ 디렉토리 확인"
        elif command -v sphinx-build &>/dev/null; then
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
    info "벤치마크 실행 중..."
    _ensure_venv dev
    echo ""
    if [ -d "tests/benchmarks" ]; then
        PY -m pytest tests/benchmarks/ --benchmark-only -v
    else
        warn "벤치마크 디렉토리를 찾을 수 없습니다."
    fi
}

run_coverage() {
    info "커버리지 리포트 생성 중..."
    _ensure_venv dev
    echo ""
    PY -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
    success "커버리지 리포트 생성 완료 - htmlcov/index.html 확인"
    local report="$SCRIPT_DIR/htmlcov/index.html"
    if [ -f "$report" ]; then
        info "리포트 열기: ./run.sh 외부에서 'xdg-open $report'"
    fi
}

run_gui() {
    print_logo
    _ensure_venv
    echo -e "${BOLD}메인프레임 GUI 시작${NC}"
    echo ""
    info "80~90년대 군사용 메인프레임 스타일 GUI"
    info "인광체: ${1:-green}"
    echo ""
    info "단축키:"
    info "  F1  - 파형 모드"
    info "  F2  - 오실로스코프 모드"
    info "  F3  - CRT 효과 토글"
    info "  F4  - 인광체 색상 변경"
    info "  ESC - 종료"
    echo ""
    if [ -z "${DISPLAY:-}" ] && [ "$IS_MACOS" = false ]; then
        warn "DISPLAY 환경변수가 없습니다. GUI는 데스크톱 세션에서 실행하세요."
    fi
    PY run_gui.py "$@"
}

show_info() {
    print_logo
    echo -e "${BOLD}시스템 정보${NC}"
    echo ""
    _resolve_python || true
    if command -v "$PYTHON_BIN" &>/dev/null; then
        echo -e "Python:        $("$PYTHON_BIN" --version 2>&1)"
        echo -e "Python 경로:   $(command -v "$PYTHON_BIN")"
    fi
    if [ -x "$VENV_DIR/bin/python" ]; then
        echo -e "venv Python:   $("$VENV_DIR/bin/python" --version 2>&1)"
    fi
    echo ""
    echo -e "${BOLD}환경${NC}"
    echo -e "OS:            $(uname -s)"
    echo -e "아키텍처:      $(uname -m)"
    if [ "$IS_JETSON" = true ]; then echo -e "플랫폼:        NVIDIA Jetson (Tegra)"; fi
    if [ "$IS_RASPBERRY_PI" = true ]; then echo -e "플랫폼:        Raspberry Pi"; fi
    if [ "$IS_WSL" = true ]; then echo -e "플랫폼:        WSL"; fi
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        TEMP=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 0)
        [ "$TEMP" -gt 0 ] && echo -e "CPU 온도:      $((TEMP/1000))°C"
    fi
    echo ""
    echo -e "${BOLD}프로젝트${NC}"
    echo -e "경로:          $SCRIPT_DIR"
    echo -e "버전:          $VERSION"
    echo -e "서버:          http://${HOST}:${PORT}"
    echo ""
    echo -e "${BOLD}가상환경${NC}"
    if [ -d "$VENV_DIR" ]; then
        echo -e "위치:          .venv/ $([ -f "$VENV_DIR/.installed" ] && echo '(설치됨)' || echo '(미설치)')"
    else
        echo -e "상태:          감지되지 않음 ('./run.sh install'로 생성)"
    fi
    echo ""
}

show_version() {
    echo "Personal Media Visualization v${VERSION}"
}

show_help() {
    print_logo
    echo -e "${BOLD}사용법:${NC} ./run.sh [명령어] [옵션]"
    echo ""
    echo -e "${BOLD}서버 명령어:${NC}"
    echo "  server      API 서버 시작 (포그라운드, 기본값)"
    echo "  serve       server 별칭 (--tunnel / --open 지원)"
    echo "  dev         개발 모드로 서버 시작 (자동 리로드)"
    echo "  start       백그라운드 데몬으로 시작"
    echo "  stop        데몬 종료"
    echo "  restart     데몬 재시작"
    echo "  status      데몬 상태 확인"
    echo "  logs        데몬 로그 follow"
    echo "  gui         메인프레임 스타일 GUI 실행"
    echo ""
    echo -e "${BOLD}개발 명령어:${NC}"
    echo "  test        테스트 실행"
    echo "  lint        코드 품질 검사 (ruff, black --check)"
    echo "  format      코드 포매팅 (black, ruff --fix)"
    echo "  check       전체 검사 (lint + type check)"
    echo "  doctor      환경/의존성 점검 (가벼움)"
    echo "  coverage    커버리지 리포트 생성"
    echo "  benchmark   벤치마크 실행"
    echo ""
    echo -e "${BOLD}빌드 명령어:${NC}"
    echo "  install     의존성 설치 (자동 venv)"
    echo "  install-dev 개발 의존성 설치"
    echo "  build       프로젝트 빌드/패키징"
    echo "  clean       캐시 및 임시 파일 정리"
    echo "  docs        문서 생성"
    echo ""
    echo -e "${BOLD}유틸리티:${NC}"
    echo "  info        시스템 정보 출력"
    echo "  version     버전 출력"
    echo "  help        이 도움말 표시"
    echo ""
    echo -e "${BOLD}서버 옵션 (server/serve/dev/start):${NC}"
    echo "  --port N                              포트 (기본값: 8000)"
    echo "  --host H                              호스트 (기본값: 0.0.0.0)"
    echo "  --tunnel [cloudflared|localhost.run]  외부 노출 터널"
    echo "  --open                                기본 브라우저로 /web 오픈"
    echo ""
    echo -e "${BOLD}환경 변수:${NC}"
    echo "  PMV_HOST    서버 호스트 (기본값: 0.0.0.0)"
    echo "  PMV_PORT    서버 포트 (기본값: 8000)"
    echo "  PYTHON      Python 실행 파일 (기본값: python3.11 -> 3.10 fallback)"
    echo ""
    echo -e "${BOLD}예시:${NC}"
    echo "  ./run.sh                          # 서버 시작"
    echo "  ./run.sh dev                      # 개발 모드"
    echo "  ./run.sh serve --tunnel --open    # 터널 + 브라우저 오픈"
    echo "  ./run.sh start                    # 백그라운드 데몬"
    echo "  ./run.sh test -k player           # 'player' 키워드 테스트만"
    echo "  PMV_PORT=9000 ./run.sh            # 포트 9000에서 시작"
    echo ""
}

# ===== 메인 실행 =====
main() {
    local cmd="${1:-server}"
    shift || true
    case "$cmd" in
        server)        start_server "$@" ;;
        serve)         start_server "$@" ;;
        dev)           start_dev_server "$@" ;;
        start)         daemon_start "$@" ;;
        stop)          daemon_stop ;;
        restart)       daemon_restart "$@" ;;
        status)        daemon_status ;;
        logs)          daemon_logs ;;
        gui)           run_gui "$@" ;;
        test)          run_tests "$@" ;;
        lint)          run_lint ;;
        format)        run_format ;;
        check)         run_check ;;
        doctor)        run_doctor ;;
        install)       install_deps ;;
        install-dev)   install_dev_deps ;;
        build)         run_build ;;
        clean)         run_clean ;;
        docs)          run_docs ;;
        benchmark)     run_benchmark ;;
        coverage)      run_coverage ;;
        info)          show_info ;;
        version|-V|--version) show_version ;;
        help|--help|-h) show_help ;;
        *)
            warn "알 수 없는 명령어: $cmd"
            echo ""
            show_help
            exit 1 ;;
    esac
}

main "$@"
