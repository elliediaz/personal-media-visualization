"""
핵심 모듈

설정 관리, 예외 처리, 로깅 등 핵심 기능을 제공합니다.
"""

from src.core.config import Config
from src.core.exceptions import (
    AnalysisException,
    APIException,
    AudioException,
    AudioFileNotFoundError,
    AudioFormatNotSupportedError,
    AudioLoadError,
    AudioPlaybackError,
    AuthenticationError,
    CacheException,
    ConfigurationException,
    FeatureExtractionError,
    InvalidConfigurationError,
    PMVException,
    RateLimitExceededError,
    RenderError,
    ShaderCompilationError,
    VisualizationException,
)

# 설정 싱글톤 인스턴스
config = Config()

__all__ = [
    "Config",
    "config",
    "PMVException",
    "AudioException",
    "AudioFileNotFoundError",
    "AudioFormatNotSupportedError",
    "AudioLoadError",
    "AudioPlaybackError",
    "AnalysisException",
    "FeatureExtractionError",
    "CacheException",
    "VisualizationException",
    "RenderError",
    "ShaderCompilationError",
    "APIException",
    "AuthenticationError",
    "RateLimitExceededError",
    "ConfigurationException",
    "InvalidConfigurationError",
]
