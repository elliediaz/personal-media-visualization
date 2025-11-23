"""
오디오 포맷 감지 단위 테스트
"""

from pathlib import Path

import pytest

from src.audio.formats import (
    AudioFormat,
    detect_format,
    get_format_info,
    get_mime_type,
    get_supported_extensions,
    is_format_supported,
)
from src.core.exceptions import AudioFormatNotSupportedError


class TestAudioFormat:
    """AudioFormat enum 테스트"""

    def test_enum_values(self):
        """Enum 값 테스트"""
        assert AudioFormat.MP3.value == "mp3"
        assert AudioFormat.WAV.value == "wav"
        assert AudioFormat.FLAC.value == "flac"
        assert AudioFormat.OGG.value == "ogg"
        assert AudioFormat.M4A.value == "m4a"
        assert AudioFormat.AAC.value == "aac"

    def test_from_extension_without_dot(self):
        """점 없는 확장자로부터 생성 테스트"""
        assert AudioFormat.from_extension("mp3") == AudioFormat.MP3
        assert AudioFormat.from_extension("wav") == AudioFormat.WAV

    def test_from_extension_with_dot(self):
        """점 있는 확장자로부터 생성 테스트"""
        assert AudioFormat.from_extension(".mp3") == AudioFormat.MP3
        assert AudioFormat.from_extension(".flac") == AudioFormat.FLAC

    def test_from_extension_case_insensitive(self):
        """대소문자 구분 없는 확장자 테스트"""
        assert AudioFormat.from_extension("MP3") == AudioFormat.MP3
        assert AudioFormat.from_extension(".WAV") == AudioFormat.WAV
        assert AudioFormat.from_extension("FlAc") == AudioFormat.FLAC

    def test_from_extension_unsupported(self):
        """지원하지 않는 확장자 테스트"""
        with pytest.raises(AudioFormatNotSupportedError) as exc_info:
            AudioFormat.from_extension("mp4")

        assert "지원하지 않는" in str(exc_info.value)

    def test_from_path(self):
        """파일 경로로부터 포맷 감지 테스트"""
        assert AudioFormat.from_path("music.mp3") == AudioFormat.MP3
        assert AudioFormat.from_path("/path/to/song.wav") == AudioFormat.WAV
        assert AudioFormat.from_path(Path("audio.flac")) == AudioFormat.FLAC

    def test_from_path_no_extension(self):
        """확장자 없는 파일 경로 테스트"""
        with pytest.raises(AudioFormatNotSupportedError) as exc_info:
            AudioFormat.from_path("filename")

        assert "확장자가 없습니다" in str(exc_info.value)


class TestFormatFunctions:
    """포맷 유틸리티 함수 테스트"""

    def test_detect_format(self):
        """포맷 감지 함수 테스트"""
        assert detect_format("song.mp3") == AudioFormat.MP3
        assert detect_format("audio.ogg") == AudioFormat.OGG

    def test_get_format_info(self):
        """포맷 정보 가져오기 테스트"""
        info = get_format_info(AudioFormat.MP3)

        assert info["name"] == "MP3"
        assert info["description"] == "MPEG-1 Audio Layer 3"
        assert info["mime_type"] == "audio/mpeg"
        assert info["codec"] == "MP3"
        assert info["lossy"] == "true"

    def test_get_format_info_wav(self):
        """WAV 포맷 정보 테스트"""
        info = get_format_info(AudioFormat.WAV)

        assert info["name"] == "WAV"
        assert info["lossy"] == "false"  # 무손실

    def test_is_format_supported_true(self):
        """지원되는 포맷 확인 테스트"""
        assert is_format_supported("music.mp3") is True
        assert is_format_supported("audio.wav") is True
        assert is_format_supported("song.flac") is True

    def test_is_format_supported_false(self):
        """지원하지 않는 포맷 확인 테스트"""
        assert is_format_supported("video.mp4") is False
        assert is_format_supported("document.pdf") is False

    def test_get_supported_extensions(self):
        """지원되는 확장자 목록 테스트"""
        extensions = get_supported_extensions()

        assert ".mp3" in extensions
        assert ".wav" in extensions
        assert ".flac" in extensions
        assert ".ogg" in extensions
        assert ".m4a" in extensions
        assert ".aac" in extensions
        assert len(extensions) == 6

    def test_get_mime_type(self):
        """MIME 타입 가져오기 테스트"""
        assert get_mime_type(AudioFormat.MP3) == "audio/mpeg"
        assert get_mime_type(AudioFormat.WAV) == "audio/wav"
        assert get_mime_type(AudioFormat.FLAC) == "audio/flac"
        assert get_mime_type(AudioFormat.OGG) == "audio/ogg"


class TestFormatMetadata:
    """포맷 메타데이터 테스트"""

    @pytest.mark.parametrize(
        "format,expected_lossy",
        [
            (AudioFormat.MP3, "true"),
            (AudioFormat.WAV, "false"),
            (AudioFormat.FLAC, "false"),
            (AudioFormat.OGG, "true"),
            (AudioFormat.M4A, "true"),
            (AudioFormat.AAC, "true"),
        ],
    )
    def test_lossy_property(self, format, expected_lossy):
        """손실/무손실 속성 테스트"""
        info = get_format_info(format)
        assert info["lossy"] == expected_lossy

    def test_all_formats_have_metadata(self):
        """모든 포맷에 메타데이터가 있는지 테스트"""
        for audio_format in AudioFormat:
            info = get_format_info(audio_format)

            assert "name" in info
            assert "description" in info
            assert "mime_type" in info
            assert "codec" in info
            assert "lossy" in info
