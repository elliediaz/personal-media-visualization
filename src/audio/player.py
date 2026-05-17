"""
오디오 플레이어

음악 파일을 재생하고 제어하는 오디오 플레이어
"""

import threading
import time
from collections.abc import Callable
from enum import Enum
from pathlib import Path

import pygame

from src.audio.formats import is_format_supported
from src.core.config import config
from src.core.exceptions import (
    AudioException,
    AudioFileNotFoundError,
    AudioLoadError,
    AudioPlaybackError,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PlayerState(Enum):
    """플레이어 상태"""

    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class AudioPlayer:
    """
    오디오 플레이어 클래스

    pygame.mixer를 사용하여 오디오 파일을 재생합니다.

    Examples:
        >>> player = AudioPlayer()
        >>> player.load("music.mp3")
        >>> player.play()
        >>> player.pause()
        >>> player.stop()
    """

    def __init__(self, config_override: dict = None):
        """
        AudioPlayer 초기화

        Args:
            config_override: 설정 오버라이드 딕셔너리
        """
        self._state = PlayerState.STOPPED
        self._file_path: Path | None = None
        self._duration: float = 0.0
        self._start_time: float = 0.0
        self._pause_position: float = 0.0
        self._volume: float = 1.0
        self._mixer_initialized = False

        # 콜백
        self._on_play: Callable | None = None
        self._on_pause: Callable | None = None
        self._on_stop: Callable | None = None
        self._on_end: Callable | None = None

        # 설정 로드
        self._config = config_override or {}
        self._sample_rate = self._config.get(
            "sample_rate", config.get("audio.sample_rate", 44100)
        )
        self._buffer_size = self._config.get(
            "buffer_size", config.get("audio.buffer_size", 2048)
        )

        # pygame.mixer 초기화
        self._init_mixer()

        # 재생 종료 이벤트 모니터링 스레드
        self._monitor_thread: threading.Thread | None = None
        self._monitoring = False

        logger.info("AudioPlayer 초기화 완료")

    def _init_mixer(self) -> None:
        """pygame.mixer 초기화"""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=self._sample_rate,
                    size=-16,  # 16-bit signed
                    channels=2,  # 스테레오
                    buffer=self._buffer_size,
                )
                self._mixer_initialized = True
                logger.debug(
                    f"pygame.mixer 초기화: {self._sample_rate}Hz, "
                    f"버퍼={self._buffer_size}"
                )
        except pygame.error as e:
            raise AudioException(f"pygame.mixer 초기화 실패: {e}") from e

    def load(self, file_path: Path | str) -> None:
        """
        오디오 파일 로드

        Args:
            file_path: 로드할 오디오 파일 경로

        Raises:
            AudioFileNotFoundError: 파일을 찾을 수 없는 경우
            AudioFormatNotSupportedError: 지원하지 않는 포맷인 경우
            AudioLoadError: 파일 로드 실패
        """
        file_path = Path(file_path)

        # 파일 존재 확인
        if not file_path.exists():
            raise AudioFileNotFoundError(
                f"오디오 파일을 찾을 수 없습니다: {file_path}",
                details={"path": str(file_path)},
            )

        # 포맷 확인
        if not is_format_supported(file_path):
            raise AudioLoadError(
                f"지원하지 않는 오디오 포맷입니다: {file_path.suffix}",
                details={"path": str(file_path), "extension": file_path.suffix},
            )

        # 기존 재생 중지
        if self._state != PlayerState.STOPPED:
            self.stop()

        try:
            # 오디오 파일 로드
            pygame.mixer.music.load(str(file_path))
            self._file_path = file_path
            self._state = PlayerState.STOPPED

            # 파일 길이 계산 (pygame.mixer는 직접 제공하지 않으므로 추정)
            # 실제 길이는 파일을 재생하면서 업데이트됨
            self._duration = self._estimate_duration(file_path)

            logger.info(f"오디오 파일 로드 완료: {file_path.name}")

        except pygame.error as e:
            raise AudioLoadError(
                f"오디오 파일 로드 실패: {e}",
                details={"path": str(file_path), "error": str(e)},
            ) from e

    def _estimate_duration(self, file_path: Path) -> float:
        """
        오디오 파일 길이 추정

        Args:
            file_path: 오디오 파일 경로

        Returns:
            예상 길이 (초)

        Note:
            pygame.mixer는 파일 길이를 직접 제공하지 않으므로,
            Phase 2에서 librosa를 사용하여 정확한 길이를 얻을 예정
        """
        # 임시로 0 반환 (Phase 2에서 librosa로 정확한 길이 계산)
        return 0.0

    def play(self, start_position: float = None) -> None:
        """
        오디오 재생 시작

        Args:
            start_position: 시작 위치 (초), None이면 현재 위치에서 시작

        Raises:
            AudioPlaybackError: 재생 실패
        """
        if self._file_path is None:
            raise AudioPlaybackError(
                "재생할 파일이 로드되지 않았습니다",
                details={"state": self._state.value},
            )

        try:
            if self._state == PlayerState.PAUSED:
                # 일시정지 상태에서 재개
                pygame.mixer.music.unpause()
                self._state = PlayerState.PLAYING
                logger.debug("재생 재개")
            else:
                # 새로 재생 시작
                if start_position is not None:
                    pygame.mixer.music.play(start=start_position)
                    self._start_time = time.time() - start_position
                else:
                    pygame.mixer.music.play()
                    self._start_time = time.time()

                self._state = PlayerState.PLAYING
                logger.info("재생 시작")

            # 볼륨 설정
            pygame.mixer.music.set_volume(self._volume)

            # 콜백 호출
            if self._on_play:
                self._on_play()

            # 재생 종료 모니터링 시작
            self._start_monitoring()

        except pygame.error as e:
            raise AudioPlaybackError(
                f"재생 시작 실패: {e}",
                details={"error": str(e)},
            ) from e

    def pause(self) -> None:
        """
        재생 일시정지

        Raises:
            AudioPlaybackError: 일시정지 실패
        """
        if self._state != PlayerState.PLAYING:
            logger.warning("재생 중이 아닙니다")
            return

        try:
            pygame.mixer.music.pause()
            self._pause_position = self.position
            self._state = PlayerState.PAUSED
            logger.debug(f"일시정지: {self._pause_position:.2f}초")

            # 콜백 호출
            if self._on_pause:
                self._on_pause()

        except pygame.error as e:
            raise AudioPlaybackError(
                f"일시정지 실패: {e}",
                details={"error": str(e)},
            ) from e

    def stop(self) -> None:
        """재생 정지"""
        if self._state == PlayerState.STOPPED:
            return

        try:
            pygame.mixer.music.stop()
            self._state = PlayerState.STOPPED
            self._start_time = 0.0
            self._pause_position = 0.0
            logger.debug("재생 정지")

            # 모니터링 중지
            self._stop_monitoring()

            # 콜백 호출
            if self._on_stop:
                self._on_stop()

        except pygame.error as e:
            raise AudioPlaybackError(
                f"재생 정지 실패: {e}",
                details={"error": str(e)},
            ) from e

    def seek(self, position: float) -> None:
        """
        재생 위치 이동

        Args:
            position: 이동할 위치 (초)

        Note:
            pygame.mixer.music.set_pos()는 일부 포맷에서만 작동하므로,
            재생을 중지하고 특정 위치에서 다시 시작하는 방식 사용
        """
        if self._file_path is None:
            raise AudioPlaybackError("파일이 로드되지 않았습니다")

        was_playing = self._state == PlayerState.PLAYING

        try:
            # 재생 중지
            pygame.mixer.music.stop()

            # 지정된 위치에서 재생 시작
            if was_playing:
                self.play(start_position=position)
            else:
                self._pause_position = position

            logger.debug(f"재생 위치 이동: {position:.2f}초")

        except pygame.error as e:
            raise AudioPlaybackError(
                f"재생 위치 이동 실패: {e}",
                details={"position": position, "error": str(e)},
            ) from e

    @property
    def duration(self) -> float:
        """
        오디오 파일 총 길이

        Returns:
            총 길이 (초)
        """
        return self._duration

    @property
    def position(self) -> float:
        """
        현재 재생 위치

        Returns:
            현재 위치 (초)
        """
        if self._state == PlayerState.PLAYING:
            return time.time() - self._start_time
        elif self._state == PlayerState.PAUSED:
            return self._pause_position
        else:
            return 0.0

    @property
    def volume(self) -> float:
        """
        현재 볼륨

        Returns:
            볼륨 (0.0 ~ 1.0)
        """
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        """
        볼륨 설정

        Args:
            value: 설정할 볼륨 (0.0 ~ 1.0)
        """
        self._volume = max(0.0, min(1.0, value))
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(self._volume)
        logger.debug(f"볼륨 설정: {self._volume:.2f}")

    @property
    def is_playing(self) -> bool:
        """
        재생 중 여부

        Returns:
            재생 중이면 True
        """
        return self._state == PlayerState.PLAYING

    @property
    def state(self) -> PlayerState:
        """
        현재 플레이어 상태

        Returns:
            PlayerState
        """
        return self._state

    @property
    def file_path(self) -> Path | None:
        """
        현재 로드된 파일 경로

        Returns:
            파일 경로 또는 None
        """
        return self._file_path

    def set_callback(
        self,
        on_play: Callable = None,
        on_pause: Callable = None,
        on_stop: Callable = None,
        on_end: Callable = None,
    ) -> None:
        """
        이벤트 콜백 설정

        Args:
            on_play: 재생 시작 시 호출될 함수
            on_pause: 일시정지 시 호출될 함수
            on_stop: 정지 시 호출될 함수
            on_end: 재생 종료 시 호출될 함수
        """
        if on_play:
            self._on_play = on_play
        if on_pause:
            self._on_pause = on_pause
        if on_stop:
            self._on_stop = on_stop
        if on_end:
            self._on_end = on_end

        logger.debug("콜백 설정 완료")

    def _start_monitoring(self) -> None:
        """재생 종료 모니터링 시작"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_playback, daemon=True)
        self._monitor_thread.start()

    def _stop_monitoring(self) -> None:
        """재생 종료 모니터링 중지"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None

    def _monitor_playback(self) -> None:
        """재생 종료 모니터링 (별도 스레드)"""
        while self._monitoring:
            if self._state == PlayerState.PLAYING:
                if not pygame.mixer.music.get_busy():
                    # 재생 종료됨
                    self._state = PlayerState.STOPPED
                    logger.info("재생 종료")

                    # 콜백 호출
                    if self._on_end:
                        self._on_end()

                    break

            time.sleep(0.1)  # 100ms마다 체크

    def get_audio_data(self) -> tuple:
        """
        오디오 데이터 반환 (librosa 사용)

        Returns:
            (audio_data, sample_rate) 튜플

        Raises:
            AudioException: 파일이 로드되지 않은 경우
        """
        if self._file_path is None:
            raise AudioException("로드된 파일이 없습니다")

        try:
            import librosa

            y, sr = librosa.load(str(self._file_path), sr=self._sample_rate)
            logger.debug(f"오디오 데이터 로드: shape={y.shape}, sr={sr}")
            return y, sr

        except Exception as e:
            raise AudioException(f"오디오 데이터 로드 실패: {e}") from e

    def get_duration_accurate(self) -> float:
        """
        정확한 오디오 길이 반환 (librosa 사용)

        Returns:
            길이 (초)

        Raises:
            AudioException: 파일이 로드되지 않은 경우
        """
        if self._file_path is None:
            raise AudioException("로드된 파일이 없습니다")

        try:
            import librosa

            duration = librosa.get_duration(path=str(self._file_path))
            self._duration = duration  # 캐시 업데이트
            logger.debug(f"정확한 길이: {duration:.2f}초")
            return duration

        except Exception as e:
            raise AudioException(f"길이 계산 실패: {e}") from e

    def __del__(self):
        """소멸자: 리소스 정리"""
        try:
            self.stop()
            self._stop_monitoring()
        except Exception:
            pass
