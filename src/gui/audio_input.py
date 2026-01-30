"""
오디오 입력 모듈

파일 로드, 시스템 오디오 캡처, 마이크 입력을 지원합니다.
"""

import sys
import queue
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Tuple, List

import numpy as np

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


class AudioInputType(Enum):
    """오디오 입력 타입"""
    NONE = "none"
    FILE = "file"
    MICROPHONE = "microphone"
    LOOPBACK = "loopback"  # 시스템 오디오
    DEMO = "demo"  # 데모 모드


@dataclass
class AudioDevice:
    """오디오 디바이스 정보"""
    index: int
    name: str
    channels: int
    sample_rate: float
    is_input: bool
    is_loopback: bool = False


@dataclass
class AudioState:
    """오디오 상태"""
    input_type: AudioInputType
    device_name: str
    sample_rate: int
    channels: int
    is_playing: bool
    position: float  # 0.0 ~ 1.0
    duration: float  # seconds
    file_path: Optional[str] = None


class BaseAudioInput(ABC):
    """오디오 입력 베이스 클래스"""

    def __init__(self, sample_rate: int = 44100, buffer_size: int = 2048):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.is_running = False
        self._waveform = np.zeros(buffer_size)
        self._spectrum = np.zeros(64)
        self._lock = threading.Lock()

    @abstractmethod
    def start(self):
        """입력 시작"""
        pass

    @abstractmethod
    def stop(self):
        """입력 중지"""
        pass

    @abstractmethod
    def get_state(self) -> AudioState:
        """현재 상태 반환"""
        pass

    def get_waveform(self) -> np.ndarray:
        """파형 데이터 반환"""
        with self._lock:
            return self._waveform.copy()

    def get_spectrum(self) -> np.ndarray:
        """스펙트럼 데이터 반환"""
        with self._lock:
            return self._spectrum.copy()

    def _compute_spectrum(self, waveform: np.ndarray, num_bands: int = 64) -> np.ndarray:
        """스펙트럼 계산"""
        if len(waveform) < 2:
            return np.zeros(num_bands)

        # FFT 계산
        fft = np.abs(np.fft.rfft(waveform))

        # 주파수 대역으로 그룹화 (로그 스케일)
        spectrum = np.zeros(num_bands)
        fft_len = len(fft)

        for i in range(num_bands):
            # 로그 스케일 인덱스
            low = int(fft_len * (2 ** (i / num_bands * 4) - 1) / 15)
            high = int(fft_len * (2 ** ((i + 1) / num_bands * 4) - 1) / 15)
            high = max(low + 1, min(high, fft_len))

            if low < fft_len:
                spectrum[i] = np.mean(fft[low:high])

        # 정규화
        max_val = np.max(spectrum)
        if max_val > 0:
            spectrum = spectrum / max_val

        return spectrum


class DemoAudioInput(BaseAudioInput):
    """데모 오디오 입력 (테스트용 합성 파형)"""

    def __init__(self, sample_rate: int = 44100, buffer_size: int = 2048):
        super().__init__(sample_rate, buffer_size)
        self._phase = 0
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """데모 시작"""
        if self.is_running:
            return

        self.is_running = True
        self._thread = threading.Thread(target=self._generate_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """데모 중지"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def get_state(self) -> AudioState:
        return AudioState(
            input_type=AudioInputType.DEMO,
            device_name="Demo Generator",
            sample_rate=self.sample_rate,
            channels=1,
            is_playing=self.is_running,
            position=0.0,
            duration=0.0,
        )

    def _generate_loop(self):
        """데모 파형 생성 루프"""
        while self.is_running:
            t = np.linspace(0, 4 * np.pi, self.buffer_size)

            # 여러 주파수 조합
            waveform = (
                np.sin(t + self._phase) * 0.4 +
                np.sin(t * 2.5 + self._phase * 1.3) * 0.25 +
                np.sin(t * 4.1 + self._phase * 0.7) * 0.15 +
                np.sin(t * 7.3 + self._phase * 2.1) * 0.1 +
                np.random.randn(self.buffer_size) * 0.05
            )

            # 엔벨로프 적용
            envelope = 0.5 + 0.5 * np.sin(self._phase * 0.1)
            waveform *= envelope

            self._phase += 0.15

            with self._lock:
                self._waveform = waveform
                self._spectrum = self._compute_spectrum(waveform)

            time.sleep(1.0 / 60)  # ~60fps


class FileAudioInput(BaseAudioInput):
    """파일 기반 오디오 입력"""

    def __init__(self, sample_rate: int = 44100, buffer_size: int = 2048):
        super().__init__(sample_rate, buffer_size)
        self._audio_data: Optional[np.ndarray] = None
        self._position = 0
        self._duration = 0.0
        self._file_path: Optional[str] = None
        self._thread: Optional[threading.Thread] = None
        self._paused = False

    def load_file(self, file_path: str) -> bool:
        """오디오 파일 로드"""
        path = Path(file_path)
        if not path.exists():
            return False

        try:
            if LIBROSA_AVAILABLE:
                # librosa로 로드 (리샘플링 지원)
                audio, sr = librosa.load(str(path), sr=self.sample_rate, mono=True)
                self._audio_data = audio
            elif SOUNDFILE_AVAILABLE:
                # soundfile로 로드
                audio, sr = sf.read(str(path))
                if len(audio.shape) > 1:
                    audio = np.mean(audio, axis=1)  # 모노로 변환

                # 리샘플링 필요시
                if sr != self.sample_rate:
                    # 간단한 리샘플링 (품질 낮음)
                    ratio = self.sample_rate / sr
                    new_len = int(len(audio) * ratio)
                    indices = np.linspace(0, len(audio) - 1, new_len).astype(int)
                    audio = audio[indices]

                self._audio_data = audio
            else:
                return False

            self._file_path = str(path)
            self._duration = len(self._audio_data) / self.sample_rate
            self._position = 0

            return True

        except Exception as e:
            print(f"파일 로드 오류: {e}")
            return False

    def start(self):
        """재생 시작"""
        if self._audio_data is None or self.is_running:
            return

        self.is_running = True
        self._paused = False
        self._thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """재생 중지"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def pause(self):
        """일시정지"""
        self._paused = True

    def resume(self):
        """재개"""
        self._paused = False

    def seek(self, position: float):
        """탐색 (0.0 ~ 1.0)"""
        if self._audio_data is not None:
            self._position = int(position * len(self._audio_data))

    def get_state(self) -> AudioState:
        position_ratio = 0.0
        if self._audio_data is not None and len(self._audio_data) > 0:
            position_ratio = self._position / len(self._audio_data)

        return AudioState(
            input_type=AudioInputType.FILE,
            device_name="File Player",
            sample_rate=self.sample_rate,
            channels=1,
            is_playing=self.is_running and not self._paused,
            position=position_ratio,
            duration=self._duration,
            file_path=self._file_path,
        )

    def _playback_loop(self):
        """재생 루프"""
        while self.is_running:
            if self._paused or self._audio_data is None:
                time.sleep(0.01)
                continue

            # 현재 위치에서 버퍼 추출
            end_pos = min(self._position + self.buffer_size, len(self._audio_data))

            if self._position >= len(self._audio_data):
                # 파일 끝 - 루프 또는 정지
                self._position = 0
                continue

            waveform = self._audio_data[self._position:end_pos]

            # 버퍼가 짧으면 패딩
            if len(waveform) < self.buffer_size:
                waveform = np.pad(waveform, (0, self.buffer_size - len(waveform)))

            with self._lock:
                self._waveform = waveform
                self._spectrum = self._compute_spectrum(waveform)

            self._position += self.buffer_size // 2  # 50% 오버랩

            # 실시간에 맞게 대기
            time.sleep(self.buffer_size / self.sample_rate / 2)


class DeviceAudioInput(BaseAudioInput):
    """디바이스 오디오 입력 (마이크/루프백)"""

    def __init__(self, sample_rate: int = 44100, buffer_size: int = 2048):
        super().__init__(sample_rate, buffer_size)
        self._device_index: Optional[int] = None
        self._device_name = "Unknown"
        self._stream: Optional[sd.InputStream] = None
        self._is_loopback = False

    @staticmethod
    def get_input_devices() -> List[AudioDevice]:
        """입력 디바이스 목록 반환"""
        devices = []

        if not SOUNDDEVICE_AVAILABLE:
            return devices

        try:
            device_list = sd.query_devices()
            for i, dev in enumerate(device_list):
                if dev['max_input_channels'] > 0:
                    is_loopback = 'loopback' in dev['name'].lower() or 'stereo mix' in dev['name'].lower()
                    devices.append(AudioDevice(
                        index=i,
                        name=dev['name'],
                        channels=dev['max_input_channels'],
                        sample_rate=dev['default_samplerate'],
                        is_input=True,
                        is_loopback=is_loopback,
                    ))
        except Exception as e:
            print(f"디바이스 조회 오류: {e}")

        return devices

    def set_device(self, device_index: int) -> bool:
        """입력 디바이스 설정"""
        if not SOUNDDEVICE_AVAILABLE:
            return False

        try:
            devices = sd.query_devices()
            if 0 <= device_index < len(devices):
                dev = devices[device_index]
                if dev['max_input_channels'] > 0:
                    self._device_index = device_index
                    self._device_name = dev['name']
                    self._is_loopback = 'loopback' in dev['name'].lower() or 'stereo mix' in dev['name'].lower()
                    return True
        except Exception as e:
            print(f"디바이스 설정 오류: {e}")

        return False

    def start(self):
        """캡처 시작"""
        if not SOUNDDEVICE_AVAILABLE or self._device_index is None:
            return

        if self.is_running:
            return

        try:
            self._stream = sd.InputStream(
                device=self._device_index,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                callback=self._audio_callback,
            )
            self._stream.start()
            self.is_running = True
        except Exception as e:
            print(f"오디오 스트림 시작 오류: {e}")

    def stop(self):
        """캡처 중지"""
        self.is_running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def get_state(self) -> AudioState:
        input_type = AudioInputType.LOOPBACK if self._is_loopback else AudioInputType.MICROPHONE

        return AudioState(
            input_type=input_type,
            device_name=self._device_name,
            sample_rate=self.sample_rate,
            channels=1,
            is_playing=self.is_running,
            position=0.0,
            duration=0.0,
        )

    def _audio_callback(self, indata, frames, time_info, status):
        """오디오 콜백"""
        if status:
            print(f"오디오 상태: {status}")

        waveform = indata[:, 0].copy()

        with self._lock:
            self._waveform = waveform
            self._spectrum = self._compute_spectrum(waveform)


class AudioInputManager:
    """오디오 입력 관리자"""

    def __init__(self, sample_rate: int = 44100, buffer_size: int = 2048):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

        self._current_input: Optional[BaseAudioInput] = None
        self._current_type = AudioInputType.NONE

        # 데모 모드로 시작
        self._demo_input = DemoAudioInput(sample_rate, buffer_size)
        self._file_input = FileAudioInput(sample_rate, buffer_size)
        self._device_input = DeviceAudioInput(sample_rate, buffer_size)

    def start_demo(self):
        """데모 모드 시작"""
        self.stop()
        self._current_input = self._demo_input
        self._current_type = AudioInputType.DEMO
        self._current_input.start()

    def load_file(self, file_path: str) -> bool:
        """파일 로드 및 재생"""
        self.stop()

        if self._file_input.load_file(file_path):
            self._current_input = self._file_input
            self._current_type = AudioInputType.FILE
            self._current_input.start()
            return True

        return False

    def start_device(self, device_index: int) -> bool:
        """디바이스 입력 시작"""
        self.stop()

        if self._device_input.set_device(device_index):
            self._current_input = self._device_input
            self._current_type = self._device_input.get_state().input_type
            self._current_input.start()
            return True

        return False

    def stop(self):
        """현재 입력 중지"""
        if self._current_input:
            self._current_input.stop()
            self._current_input = None
            self._current_type = AudioInputType.NONE

    def pause(self):
        """일시정지 (파일만)"""
        if isinstance(self._current_input, FileAudioInput):
            self._current_input.pause()

    def resume(self):
        """재개 (파일만)"""
        if isinstance(self._current_input, FileAudioInput):
            self._current_input.resume()

    def seek(self, position: float):
        """탐색 (파일만)"""
        if isinstance(self._current_input, FileAudioInput):
            self._current_input.seek(position)

    def get_waveform(self) -> np.ndarray:
        """현재 파형"""
        if self._current_input:
            return self._current_input.get_waveform()
        return np.zeros(self.buffer_size)

    def get_spectrum(self) -> np.ndarray:
        """현재 스펙트럼"""
        if self._current_input:
            return self._current_input.get_spectrum()
        return np.zeros(64)

    def get_state(self) -> AudioState:
        """현재 상태"""
        if self._current_input:
            return self._current_input.get_state()

        return AudioState(
            input_type=AudioInputType.NONE,
            device_name="No Input",
            sample_rate=self.sample_rate,
            channels=0,
            is_playing=False,
            position=0.0,
            duration=0.0,
        )

    @staticmethod
    def get_input_devices() -> List[AudioDevice]:
        """입력 디바이스 목록"""
        return DeviceAudioInput.get_input_devices()

    @staticmethod
    def get_supported_formats() -> List[str]:
        """지원하는 오디오 포맷"""
        formats = []
        if LIBROSA_AVAILABLE:
            formats.extend([".mp3", ".wav", ".flac", ".ogg", ".m4a"])
        elif SOUNDFILE_AVAILABLE:
            formats.extend([".wav", ".flac", ".ogg"])
        return formats
