"""
오디오-색상 매핑 시스템

오디오 특성을 색상으로 매핑합니다.
"""

import colorsys

import numpy as np

from src.analysis.result import AnalysisResult
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ColorMapper:
    """
    오디오 특성을 색상으로 매핑하는 클래스

    다양한 매핑 전략을 제공합니다.
    """

    def __init__(self):
        """ColorMapper 초기화"""
        logger.debug("ColorMapper 초기화")

    def frequency_to_hue(self, frequency: float, min_freq: float = 20, max_freq: float = 20000) -> float:
        """
        주파수를 색조(Hue)로 매핑

        Args:
            frequency: 주파수 (Hz)
            min_freq: 최소 주파수
            max_freq: 최대 주파수

        Returns:
            색조 값 (0.0 ~ 1.0)
        """
        # 로그 스케일 매핑
        log_freq = np.log10(np.clip(frequency, min_freq, max_freq))
        log_min = np.log10(min_freq)
        log_max = np.log10(max_freq)

        hue = (log_freq - log_min) / (log_max - log_min)
        return np.clip(hue, 0.0, 1.0)

    def amplitude_to_brightness(self, amplitude: float, min_amp: float = 0.0, max_amp: float = 1.0) -> float:
        """
        진폭을 밝기로 매핑

        Args:
            amplitude: 진폭
            min_amp: 최소 진폭
            max_amp: 최대 진폭

        Returns:
            밝기 값 (0.0 ~ 1.0)
        """
        normalized = (amplitude - min_amp) / (max_amp - min_amp)
        return np.clip(normalized, 0.0, 1.0)

    def energy_to_saturation(self, energy: float, min_energy: float = 0.0, max_energy: float = 1.0) -> float:
        """
        에너지를 채도로 매핑

        Args:
            energy: 에너지 값
            min_energy: 최소 에너지
            max_energy: 최대 에너지

        Returns:
            채도 값 (0.0 ~ 1.0)
        """
        normalized = (energy - min_energy) / (max_energy - min_energy)
        return np.clip(normalized, 0.3, 1.0)  # 최소 채도 0.3 유지

    def hsv_to_rgb(self, h: float, s: float, v: float) -> tuple[float, float, float]:
        """
        HSV를 RGB로 변환

        Args:
            h: 색조 (0.0 ~ 1.0)
            s: 채도 (0.0 ~ 1.0)
            v: 명도 (0.0 ~ 1.0)

        Returns:
            (r, g, b) 튜플 (0.0 ~ 1.0)
        """
        return colorsys.hsv_to_rgb(h, s, v)

    def spectral_centroid_to_color(
        self, centroid: float, min_cent: float = 0, max_cent: float = 8000
    ) -> tuple[float, float, float]:
        """
        Spectral centroid를 색상으로 변환

        Args:
            centroid: Spectral centroid 값
            min_cent: 최소값
            max_cent: 최대값

        Returns:
            (r, g, b) 튜플
        """
        hue = self.frequency_to_hue(centroid, min_cent, max_cent)
        return self.hsv_to_rgb(hue, 0.8, 0.9)

    def tempo_to_hue(self, tempo: float, min_bpm: float = 60, max_bpm: float = 180) -> float:
        """
        템포를 색조로 매핑

        Args:
            tempo: 템포 (BPM)
            min_bpm: 최소 BPM
            max_bpm: 최대 BPM

        Returns:
            색조 값
        """
        normalized = (tempo - min_bpm) / (max_bpm - min_bpm)
        return np.clip(normalized, 0.0, 1.0)

    def feature_to_color(
        self,
        result: AnalysisResult,
        frame_index: int = None,
        mode: str = "spectral"
    ) -> tuple[float, float, float]:
        """
        분석 결과를 색상으로 변환

        Args:
            result: 분석 결과
            frame_index: 프레임 인덱스 (None이면 평균)
            mode: 매핑 모드 ("spectral", "rhythm", "energy")

        Returns:
            (r, g, b) 튜플
        """
        if mode == "spectral":
            # Spectral centroid 기반
            centroid = result.spectral.get("spectral_centroid")
            if centroid is not None:
                value = centroid[frame_index] if frame_index is not None else np.mean(centroid)
                return self.spectral_centroid_to_color(value)

        elif mode == "rhythm":
            # 템포 기반
            tempo = result.rhythm.get("tempo", 120)
            hue = self.tempo_to_hue(tempo)
            return self.hsv_to_rgb(hue, 0.7, 0.8)

        elif mode == "energy":
            # RMS 에너지 기반
            rms = result.timbre.get("rms_energy")
            if rms is not None:
                energy = rms[frame_index] if frame_index is not None else np.mean(rms)

                brightness = self.amplitude_to_brightness(energy)
                return self.hsv_to_rgb(0.5, 0.6, brightness)

        # 기본 색상
        return (0.5, 0.8, 0.9)

    def create_gradient(
        self,
        start_color: tuple[float, float, float],
        end_color: tuple[float, float, float],
        steps: int
    ) -> np.ndarray:
        """
        두 색상 간 그라디언트 생성

        Args:
            start_color: 시작 색상 (r, g, b)
            end_color: 끝 색상 (r, g, b)
            steps: 단계 수

        Returns:
            색상 배열 (steps, 3)
        """
        gradient = np.zeros((steps, 3))
        for i in range(3):
            gradient[:, i] = np.linspace(start_color[i], end_color[i], steps)
        return gradient

    def audio_reactive_palette(
        self,
        result: AnalysisResult,
        num_colors: int = 5
    ) -> list[tuple[float, float, float]]:
        """
        오디오 반응형 색상 팔레트 생성

        Args:
            result: 분석 결과
            num_colors: 생성할 색상 수

        Returns:
            색상 리스트
        """
        palette = []

        # 템포 기반 기본 색조
        tempo = result.rhythm.get("tempo", 120)
        base_hue = self.tempo_to_hue(tempo)

        # Spectral centroid 기반 채도
        centroid = result.spectral.get("spectral_centroid")
        if centroid is not None:
            avg_centroid = np.mean(centroid)
            saturation = np.clip(avg_centroid / 4000, 0.5, 1.0)
        else:
            saturation = 0.8

        # 색상 생성
        for i in range(num_colors):
            hue = (base_hue + i * 0.2) % 1.0
            value = 0.7 + (i * 0.05)
            palette.append(self.hsv_to_rgb(hue, saturation, value))

        return palette
