"""
오디오 포맷 감지 및 정보

지원되는 오디오 포맷을 정의하고 파일 포맷을 감지합니다.
"""

import mimetypes
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from src.core.exceptions import AudioFormatNotSupportedError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AudioFormat(Enum):
    """지원되는 오디오 포맷"""

    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    OGG = "ogg"
    M4A = "m4a"
    AAC = "aac"

    @classmethod
    def from_extension(cls, extension: str) -> "AudioFormat":
        """
        파일 확장자로부터 AudioFormat 생성

        Args:
            extension: 파일 확장자 (점 포함 또는 미포함)

        Returns:
            AudioFormat 인스턴스

        Raises:
            AudioFormatNotSupportedError: 지원하지 않는 포맷인 경우
        """
        # 점 제거 및 소문자 변환
        ext = extension.lstrip(".").lower()

        try:
            return cls(ext)
        except ValueError:
            raise AudioFormatNotSupportedError(
                f"지원하지 않는 오디오 포맷입니다: {ext}",
                details={"extension": ext, "supported": [f.value for f in cls]},
            )

    @classmethod
    def from_path(cls, file_path: Path | str) -> "AudioFormat":
        """
        파일 경로로부터 AudioFormat 감지

        Args:
            file_path: 오디오 파일 경로

        Returns:
            AudioFormat 인스턴스

        Raises:
            AudioFormatNotSupportedError: 지원하지 않는 포맷인 경우
        """
        path = Path(file_path)
        extension = path.suffix

        if not extension:
            raise AudioFormatNotSupportedError(
                f"파일 확장자가 없습니다: {file_path}",
                details={"path": str(file_path)},
            )

        return cls.from_extension(extension)


# 오디오 포맷 메타데이터
FORMAT_METADATA: Dict[AudioFormat, Dict[str, str]] = {
    AudioFormat.MP3: {
        "name": "MP3",
        "description": "MPEG-1 Audio Layer 3",
        "mime_type": "audio/mpeg",
        "codec": "MP3",
        "lossy": "true",
    },
    AudioFormat.WAV: {
        "name": "WAV",
        "description": "Waveform Audio File Format",
        "mime_type": "audio/wav",
        "codec": "PCM",
        "lossy": "false",
    },
    AudioFormat.FLAC: {
        "name": "FLAC",
        "description": "Free Lossless Audio Codec",
        "mime_type": "audio/flac",
        "codec": "FLAC",
        "lossy": "false",
    },
    AudioFormat.OGG: {
        "name": "OGG",
        "description": "Ogg Vorbis",
        "mime_type": "audio/ogg",
        "codec": "Vorbis",
        "lossy": "true",
    },
    AudioFormat.M4A: {
        "name": "M4A",
        "description": "MPEG-4 Audio",
        "mime_type": "audio/mp4",
        "codec": "AAC",
        "lossy": "true",
    },
    AudioFormat.AAC: {
        "name": "AAC",
        "description": "Advanced Audio Coding",
        "mime_type": "audio/aac",
        "codec": "AAC",
        "lossy": "true",
    },
}


def detect_format(file_path: Path | str) -> AudioFormat:
    """
    파일 경로로부터 오디오 포맷 감지

    Args:
        file_path: 오디오 파일 경로

    Returns:
        감지된 AudioFormat

    Raises:
        AudioFormatNotSupportedError: 지원하지 않는 포맷인 경우

    Examples:
        >>> format = detect_format("music.mp3")
        >>> print(format)
        AudioFormat.MP3
    """
    return AudioFormat.from_path(file_path)


def get_format_info(audio_format: AudioFormat) -> Dict[str, str]:
    """
    오디오 포맷 정보 가져오기

    Args:
        audio_format: AudioFormat 인스턴스

    Returns:
        포맷 정보 딕셔너리

    Examples:
        >>> info = get_format_info(AudioFormat.MP3)
        >>> print(info['name'])
        MP3
    """
    return FORMAT_METADATA.get(audio_format, {}).copy()


def is_format_supported(file_path: Path | str) -> bool:
    """
    파일이 지원되는 포맷인지 확인

    Args:
        file_path: 확인할 파일 경로

    Returns:
        지원 여부 (True/False)

    Examples:
        >>> is_format_supported("music.mp3")
        True
        >>> is_format_supported("video.mp4")
        False
    """
    try:
        detect_format(file_path)
        return True
    except AudioFormatNotSupportedError:
        return False


def get_supported_extensions() -> list[str]:
    """
    지원되는 모든 파일 확장자 목록 반환

    Returns:
        확장자 목록 (점 포함)

    Examples:
        >>> extensions = get_supported_extensions()
        >>> print(extensions)
        ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac']
    """
    return [f".{fmt.value}" for fmt in AudioFormat]


def get_mime_type(audio_format: AudioFormat) -> str:
    """
    오디오 포맷의 MIME 타입 반환

    Args:
        audio_format: AudioFormat 인스턴스

    Returns:
        MIME 타입 문자열

    Examples:
        >>> mime = get_mime_type(AudioFormat.MP3)
        >>> print(mime)
        audio/mpeg
    """
    info = get_format_info(audio_format)
    return info.get("mime_type", "application/octet-stream")
