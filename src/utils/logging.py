"""
로깅 유틸리티

애플리케이션 전반의 로깅 설정 및 관리
"""

import logging
import logging.handlers
import sys
from pathlib import Path

import colorlog

from src.core.config import config


def setup_logging(
    name: str = "src",
    level: str | None = None,
    log_file: Path | None = None,
) -> logging.Logger:
    """
    로거 설정

    Args:
        name: 로거 이름
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (None이면 파일 로깅 비활성화)

    Returns:
        설정된 로거
    """
    logger = logging.getLogger(name)

    # 기존 핸들러 제거
    logger.handlers.clear()

    # 로그 레벨 설정
    if level is None:
        level = config.get("app.log_level", "INFO")
    logger.setLevel(getattr(logging, level.upper()))

    # 콘솔 핸들러 (컬러 출력)
    console_handler = colorlog.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (선택적)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)

        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # 부모 로거로 전파 방지
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    로거 가져오기

    Args:
        name: 로거 이름

    Returns:
        로거 인스턴스
    """
    logger = logging.getLogger(name)

    # 로거가 핸들러가 없으면 기본 설정 적용
    if not logger.handlers:
        setup_logging(name)

    return logger


# 기본 로거
logger = setup_logging()
