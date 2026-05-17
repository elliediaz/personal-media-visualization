"""
오디오 플레이어 단위 테스트
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.audio.player import AudioPlayer, PlayerState
from src.core.exceptions import (
    AudioFileNotFoundError,
    AudioLoadError,
    AudioPlaybackError,
)


@pytest.fixture
def mock_pygame():
    """pygame.mixer Mock"""
    with patch("src.audio.player.pygame") as mock_pg:
        # pygame.error 는 실제 예외 클래스여야 except/raise 가 동작한다
        mock_pg.error = type("MockPygameError", (Exception,), {})

        # mixer 초기화 Mock
        mock_pg.mixer.get_init.return_value = None
        mock_pg.mixer.init.return_value = None

        # music Mock
        mock_pg.mixer.music.load.return_value = None
        mock_pg.mixer.music.play.return_value = None
        mock_pg.mixer.music.pause.return_value = None
        mock_pg.mixer.music.unpause.return_value = None
        mock_pg.mixer.music.stop.return_value = None
        mock_pg.mixer.music.set_volume.return_value = None
        mock_pg.mixer.music.get_busy.return_value = True

        yield mock_pg


@pytest.fixture
def temp_audio_file():
    """임시 오디오 파일 생성"""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(b"fake audio data")
        temp_path = Path(f.name)

    yield temp_path

    # 정리
    temp_path.unlink()


class TestAudioPlayerInit:
    """AudioPlayer 초기화 테스트"""

    def test_init_default(self, mock_pygame):
        """기본 초기화 테스트"""
        player = AudioPlayer()

        assert player.state == PlayerState.STOPPED
        assert player.file_path is None
        assert player.volume == 1.0
        mock_pygame.mixer.init.assert_called_once()

    def test_init_with_config(self, mock_pygame):
        """설정 오버라이드 초기화 테스트"""
        config = {"sample_rate": 48000, "buffer_size": 1024}
        player = AudioPlayer(config_override=config)

        assert player._sample_rate == 48000
        assert player._buffer_size == 1024


class TestAudioPlayerLoad:
    """AudioPlayer 파일 로드 테스트"""

    def test_load_success(self, mock_pygame, temp_audio_file):
        """파일 로드 성공 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)

        assert player.file_path == temp_audio_file
        assert player.state == PlayerState.STOPPED
        mock_pygame.mixer.music.load.assert_called_once_with(str(temp_audio_file))

    def test_load_file_not_found(self, mock_pygame):
        """파일 없음 예외 테스트"""
        player = AudioPlayer()

        with pytest.raises(AudioFileNotFoundError):
            player.load("nonexistent.mp3")

    def test_load_unsupported_format(self, mock_pygame):
        """지원하지 않는 포맷 테스트"""
        player = AudioPlayer()

        # 임시 .txt 파일 생성
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = Path(f.name)

        try:
            with pytest.raises(AudioLoadError):
                player.load(temp_path)
        finally:
            temp_path.unlink()

    def test_load_pygame_error(self, mock_pygame, temp_audio_file):
        """pygame 로드 오류 테스트"""
        mock_pygame.mixer.music.load.side_effect = mock_pygame.error("Load failed")

        player = AudioPlayer()

        with pytest.raises(AudioLoadError):
            player.load(temp_audio_file)

    def test_load_stops_current_playback(self, mock_pygame, temp_audio_file):
        """새 파일 로드 시 기존 재생 중지 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)
        player._state = PlayerState.PLAYING

        # 다른 파일 로드
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"fake wav data")
            temp_wav = Path(f.name)

        try:
            player.load(temp_wav)
            mock_pygame.mixer.music.stop.assert_called()
        finally:
            temp_wav.unlink()


class TestAudioPlayerPlayback:
    """AudioPlayer 재생 제어 테스트"""

    def test_play_without_load(self, mock_pygame):
        """파일 로드 없이 재생 시도 테스트"""
        player = AudioPlayer()

        with pytest.raises(AudioPlaybackError):
            player.play()

    def test_play_success(self, mock_pygame, temp_audio_file):
        """재생 성공 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)
        player.play()

        assert player.state == PlayerState.PLAYING
        assert player.is_playing is True
        mock_pygame.mixer.music.play.assert_called_once()

    def test_play_from_paused(self, mock_pygame, temp_audio_file):
        """일시정지 상태에서 재생 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)
        player._state = PlayerState.PAUSED

        player.play()

        assert player.state == PlayerState.PLAYING
        mock_pygame.mixer.music.unpause.assert_called_once()

    def test_pause(self, mock_pygame, temp_audio_file):
        """일시정지 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)
        player.play()

        player.pause()

        assert player.state == PlayerState.PAUSED
        mock_pygame.mixer.music.pause.assert_called_once()

    def test_pause_when_not_playing(self, mock_pygame, temp_audio_file):
        """재생 중이 아닐 때 일시정지 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)

        # 경고만 발생하고 예외는 발생하지 않음
        player.pause()
        assert player.state == PlayerState.STOPPED

    def test_stop(self, mock_pygame, temp_audio_file):
        """정지 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)
        player.play()

        player.stop()

        assert player.state == PlayerState.STOPPED
        assert player.is_playing is False
        mock_pygame.mixer.music.stop.assert_called()

    def test_stop_when_already_stopped(self, mock_pygame, temp_audio_file):
        """이미 정지된 상태에서 정지 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)

        player.stop()
        # 예외 없이 정상 동작


class TestAudioPlayerSeek:
    """AudioPlayer 탐색 테스트"""

    def test_seek_without_load(self, mock_pygame):
        """파일 로드 없이 탐색 시도 테스트"""
        player = AudioPlayer()

        with pytest.raises(AudioPlaybackError):
            player.seek(10.0)

    def test_seek_while_playing(self, mock_pygame, temp_audio_file):
        """재생 중 탐색 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)
        player.play()

        player.seek(30.0)

        # stop과 play가 호출되어야 함
        assert mock_pygame.mixer.music.stop.called
        assert mock_pygame.mixer.music.play.call_count >= 2  # 초기 play + seek play

    def test_seek_while_stopped(self, mock_pygame, temp_audio_file):
        """정지 중 탐색 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)

        player.seek(15.0)

        # pause_position만 업데이트되고 재생은 시작하지 않음
        assert player._pause_position == 15.0


class TestAudioPlayerProperties:
    """AudioPlayer 속성 테스트"""

    def test_volume_get(self, mock_pygame):
        """볼륨 가져오기 테스트"""
        player = AudioPlayer()
        assert player.volume == 1.0

    def test_volume_set(self, mock_pygame, temp_audio_file):
        """볼륨 설정 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)

        player.volume = 0.5
        assert player.volume == 0.5

        player.volume = 1.5  # 범위 초과
        assert player.volume == 1.0  # 클램핑됨

        player.volume = -0.5  # 범위 미만
        assert player.volume == 0.0  # 클램핑됨

    def test_duration(self, mock_pygame, temp_audio_file):
        """길이 속성 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)

        # 현재는 0.0 (Phase 2에서 실제 길이 계산)
        assert player.duration >= 0.0

    def test_position_when_stopped(self, mock_pygame, temp_audio_file):
        """정지 상태 위치 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)

        assert player.position == 0.0

    def test_position_when_playing(self, mock_pygame, temp_audio_file):
        """재생 중 위치 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)
        player.play()

        time.sleep(0.1)
        assert player.position > 0.0

    def test_state_property(self, mock_pygame, temp_audio_file):
        """상태 속성 테스트"""
        player = AudioPlayer()
        assert player.state == PlayerState.STOPPED

        player.load(temp_audio_file)
        assert player.state == PlayerState.STOPPED

        player.play()
        assert player.state == PlayerState.PLAYING

        player.pause()
        assert player.state == PlayerState.PAUSED

        player.stop()
        assert player.state == PlayerState.STOPPED

    def test_file_path_property(self, mock_pygame, temp_audio_file):
        """파일 경로 속성 테스트"""
        player = AudioPlayer()
        assert player.file_path is None

        player.load(temp_audio_file)
        assert player.file_path == temp_audio_file


class TestAudioPlayerCallbacks:
    """AudioPlayer 콜백 테스트"""

    def test_on_play_callback(self, mock_pygame, temp_audio_file):
        """재생 시작 콜백 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)

        callback = Mock()
        player.set_callback(on_play=callback)

        player.play()
        callback.assert_called_once()

    def test_on_pause_callback(self, mock_pygame, temp_audio_file):
        """일시정지 콜백 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)
        player.play()

        callback = Mock()
        player.set_callback(on_pause=callback)

        player.pause()
        callback.assert_called_once()

    def test_on_stop_callback(self, mock_pygame, temp_audio_file):
        """정지 콜백 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)
        player.play()

        callback = Mock()
        player.set_callback(on_stop=callback)

        player.stop()
        callback.assert_called_once()

    def test_on_end_callback(self, mock_pygame, temp_audio_file):
        """재생 종료 콜백 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)

        callback = Mock()
        player.set_callback(on_end=callback)

        # 재생 시작
        player.play()

        # 재생 종료 시뮬레이션
        mock_pygame.mixer.music.get_busy.return_value = False
        time.sleep(0.2)  # 모니터링 스레드가 감지할 시간

        # 콜백이 호출되었는지 확인
        callback.assert_called_once()

    def test_multiple_callbacks(self, mock_pygame, temp_audio_file):
        """여러 콜백 동시 설정 테스트"""
        player = AudioPlayer()
        player.load(temp_audio_file)

        on_play_callback = Mock()
        on_stop_callback = Mock()

        player.set_callback(on_play=on_play_callback, on_stop=on_stop_callback)

        player.play()
        on_play_callback.assert_called_once()

        player.stop()
        on_stop_callback.assert_called_once()
