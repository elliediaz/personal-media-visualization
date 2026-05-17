"""
FastAPI 애플리케이션

REST API 및 WebSocket 서버
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api.models import ErrorResponse, HealthResponse
from src.core.config import Config
from src.utils.logging import get_logger, setup_logging

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 로깅 설정
setup_logging("api")
logger = get_logger(__name__)

# 설정
config = Config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리

    Args:
        app: FastAPI 애플리케이션
    """
    # 시작
    logger.info("=" * 60)
    logger.info("Personal Media Visualization API 시작")
    logger.info(f"버전: {config.get('api.version', '1.0.0')}")
    logger.info(f"호스트: {config.get('api.host', '0.0.0.0')}")
    logger.info(f"포트: {config.get('api.port', 8000)}")
    logger.info("=" * 60)

    yield

    # 종료
    logger.info("API 서버 종료")


# FastAPI 애플리케이션
app = FastAPI(
    title="Personal Media Visualization API",
    description="오디오 분석 및 시각화 REST API",
    version=config.get("api.version", "1.0.0"),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ===== CORS 설정 =====


def setup_cors():
    """CORS 미들웨어 설정"""
    cors_enabled = config.get("api.cors.enabled", True)

    if not cors_enabled:
        logger.info("CORS 비활성화")
        return

    origins = config.get("api.cors.origins", ["*"])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info(f"CORS 활성화: {origins}")


setup_cors()


# ===== 미들웨어 =====


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    요청 로깅 미들웨어

    Args:
        request: HTTP 요청
        call_next: 다음 미들웨어/핸들러

    Returns:
        HTTP 응답
    """
    start_time = time.time()

    # 요청 정보
    client_host = request.client.host if request.client else "unknown"
    method = request.method
    url = str(request.url)

    logger.info(f"요청: {method} {url} from {client_host}")

    # 처리
    response = await call_next(request)

    # 응답 시간
    duration = time.time() - start_time
    logger.info(
        f"응답: {method} {url} - {response.status_code} ({duration:.3f}s)"
    )

    # 응답 헤더에 처리 시간 추가
    response.headers["X-Process-Time"] = str(duration)

    return response


# ===== 예외 핸들러 =====


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """
    요청 검증 에러 핸들러

    Args:
        request: HTTP 요청
        exc: 검증 예외

    Returns:
        JSON 에러 응답
    """
    logger.warning(f"검증 에러: {exc.errors()}")

    error_response = ErrorResponse(
        error="ValidationError",
        message="요청 데이터 검증 실패",
        details={"errors": exc.errors()},
        timestamp=datetime.now(),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    일반 예외 핸들러

    Args:
        request: HTTP 요청
        exc: 예외

    Returns:
        JSON 에러 응답
    """
    logger.error(f"서버 에러: {exc}", exc_info=True)

    error_response = ErrorResponse(
        error="InternalServerError",
        message="서버 내부 오류가 발생했습니다",
        details={"exception": str(exc)},
        timestamp=datetime.now(),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )


# ===== 기본 엔드포인트 =====


@app.get("/", response_model=dict[str, str])
async def root():
    """
    루트 엔드포인트

    Returns:
        환영 메시지
    """
    return {
        "message": "Personal Media Visualization API",
        "version": config.get("api.version", "1.0.0"),
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    헬스체크 엔드포인트

    Returns:
        시스템 상태
    """
    return HealthResponse(
        status="healthy",
        version=config.get("api.version", "1.0.0"),
        timestamp=datetime.now(),
    )


# ===== 라우터 등록 =====


def register_routers():
    """API 라우터 등록"""
    try:
        from src.api.routes import analysis, audio, visualization

        app.include_router(
            audio.router,
            prefix="/api/v1/audio",
            tags=["Audio"]
        )

        app.include_router(
            analysis.router,
            prefix="/api/v1/analysis",
            tags=["Analysis"]
        )

        app.include_router(
            visualization.router,
            prefix="/api/v1/visualize",
            tags=["Visualization"]
        )

        logger.info("API 라우터 등록 완료")

    except ImportError as e:
        logger.warning(f"라우터 import 실패 (아직 구현되지 않음): {e}")


register_routers()


# ===== WebSocket 등록 =====


def register_websockets():
    """WebSocket 엔드포인트 등록"""
    try:
        from src.api.websocket import router as ws_router

        app.include_router(ws_router)
        logger.info("WebSocket 엔드포인트 등록 완료")

    except ImportError as e:
        logger.warning(f"WebSocket import 실패 (아직 구현되지 않음): {e}")


register_websockets()


# ===== 정적 파일 및 템플릿 =====


def setup_static_files():
    """정적 파일 서빙 설정"""
    static_path = PROJECT_ROOT / "static"
    output_path = PROJECT_ROOT / "output"

    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        logger.info(f"정적 파일 서빙: {static_path}")

    if output_path.exists():
        app.mount("/output", StaticFiles(directory=str(output_path)), name="output")
        logger.info(f"출력 파일 서빙: {output_path}")


setup_static_files()

# 템플릿 설정
templates_path = PROJECT_ROOT / "templates"
templates = Jinja2Templates(directory=str(templates_path)) if templates_path.exists() else None


@app.get("/web", response_class=HTMLResponse)
async def web_index(request: Request):
    """
    웹 인터페이스 메인 페이지

    Returns:
        HTML 페이지
    """
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>PMViz</title></head>
        <body>
            <h1>Personal Media Visualization</h1>
            <p>API 문서: <a href="/docs">/docs</a></p>
        </body>
        </html>
        """)
