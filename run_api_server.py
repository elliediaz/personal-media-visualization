"""
API 서버 실행

FastAPI 서버 시작
"""

import uvicorn

from src.core.config import Config

if __name__ == "__main__":
    config = Config()

    host = config.get("api.host", "0.0.0.0")
    port = config.get("api.port", 8000)
    reload = config.get("api.reload", False)

    uvicorn.run(
        "src.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
