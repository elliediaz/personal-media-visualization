"""
사용자 정의 예외 클래스들

애플리케이션 전반에서 사용되는 커스텀 예외를 정의합니다.
"""


class PMVException(Exception):
    """모든 PMV 예외의 기본 클래스"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AudioException(PMVException):
    """오디오 관련 예외"""

    pass


class AudioFileNotFoundError(AudioException):
    """오디오 파일을 찾을 수 없을 때"""

    pass


class AudioFormatNotSupportedError(AudioException):
    """지원하지 않는 오디오 포맷일 때"""

    pass


class AudioLoadError(AudioException):
    """오디오 파일 로드 실패 시"""

    pass


class AudioPlaybackError(AudioException):
    """오디오 재생 중 오류 발생 시"""

    pass


class AnalysisException(PMVException):
    """분석 관련 예외"""

    pass


class FeatureExtractionError(AnalysisException):
    """특성 추출 실패 시"""

    pass


class CacheException(PMVException):
    """캐시 관련 예외"""

    pass


class VisualizationException(PMVException):
    """시각화 관련 예외"""

    pass


class RenderError(VisualizationException):
    """렌더링 실패 시"""

    pass


class ShaderCompilationError(VisualizationException):
    """쉐이더 컴파일 실패 시"""

    pass


class APIException(PMVException):
    """API 관련 예외"""

    pass


class AuthenticationError(APIException):
    """인증 실패 시"""

    pass


class RateLimitExceededError(APIException):
    """요청 제한 초과 시"""

    pass


class ConfigurationException(PMVException):
    """설정 관련 예외"""

    pass


class InvalidConfigurationError(ConfigurationException):
    """잘못된 설정값"""

    pass
