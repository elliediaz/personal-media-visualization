"""
예술적 시각화 기본 클래스

오디오 반응형 예술적 시각화를 위한 기본 클래스
레트로 CRT 효과 및 팔레트 통합 지원
"""

import numpy as np
from pathlib import Path

from src.analysis.result import AnalysisResult
from src.visualization.artistic.color_mapping import ColorMapper
from src.visualization.base import BaseVisualizer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RetroMixin:
    """
    레트로 효과 믹스인

    기존 시각화 클래스에 레트로 기능을 추가하기 위한 믹스인
    """

    def apply_retro_palette(self, palette_name: str = "synthwave"):
        """
        레트로 팔레트 적용

        Args:
            palette_name: 팔레트 이름
        """
        try:
            from src.visualization.retro.color_palettes import RetroPalettes
            self._retro_palette = RetroPalettes.get_palette(palette_name)
            self._retro_palette_name = palette_name
            logger.debug(f"레트로 팔레트 적용: {palette_name}")
        except ImportError:
            logger.warning("레트로 팔레트 모듈을 찾을 수 없음")
            self._retro_palette = None

    def get_retro_color(self, index: int) -> tuple:
        """
        레트로 팔레트에서 색상 가져오기

        Args:
            index: 색상 인덱스

        Returns:
            (R, G, B) 튜플 (0-1 범위)
        """
        if hasattr(self, '_retro_palette') and self._retro_palette is not None:
            palette = self._retro_palette
            color = palette[index % len(palette)]
            return (color[0] / 255, color[1] / 255, color[2] / 255)
        return (1.0, 1.0, 1.0)

    def quantize_image_to_palette(self, image: np.ndarray) -> np.ndarray:
        """
        이미지를 레트로 팔레트로 양자화

        Args:
            image: 입력 이미지 (RGB, 0-255)

        Returns:
            양자화된 이미지
        """
        if not hasattr(self, '_retro_palette') or self._retro_palette is None:
            return image

        try:
            from src.visualization.retro.color_palettes import quantize_to_palette
            return quantize_to_palette(image, self._retro_palette)
        except ImportError:
            return image

    def enable_scanline_effect(self, intensity: float = 0.3):
        """
        스캔라인 효과 활성화

        Args:
            intensity: 효과 강도 (0.0-1.0)
        """
        self._scanline_enabled = True
        self._scanline_intensity = np.clip(intensity, 0.0, 1.0)

    def disable_scanline_effect(self):
        """스캔라인 효과 비활성화"""
        self._scanline_enabled = False

    def apply_scanlines_to_image(self, image: np.ndarray) -> np.ndarray:
        """
        이미지에 스캔라인 효과 적용

        Args:
            image: 입력 이미지

        Returns:
            스캔라인이 적용된 이미지
        """
        if not getattr(self, '_scanline_enabled', False):
            return image

        intensity = getattr(self, '_scanline_intensity', 0.3)
        result = image.astype(np.float64)

        # 짝수 행에 어둡게 처리
        result[::2, :] *= (1.0 - intensity)

        return np.clip(result, 0, 255).astype(np.uint8)


class BaseArtisticVisualizer(BaseVisualizer):
    """
    예술적 시각화 기본 클래스

    오디오 특성에 반응하는 예술적 효과의 기반 클래스
    """

    def __init__(self, config_override: dict = None):
        """
        BaseArtisticVisualizer 초기화

        Args:
            config_override: 설정 오버라이드
        """
        super().__init__(config_override)

        # 색상 매퍼
        self.color_mapper = ColorMapper()

        # 애니메이션 프레임 수
        self.num_frames = config_override.get("num_frames", 100) if config_override else 100

        logger.debug(f"{self.__class__.__name__} 초기화")

    def normalize_feature(
        self,
        feature: np.ndarray,
        min_val: float = None,
        max_val: float = None
    ) -> np.ndarray:
        """
        특성을 0~1 범위로 정규화

        Args:
            feature: 특성 배열
            min_val: 최소값 (None이면 자동)
            max_val: 최대값 (None이면 자동)

        Returns:
            정규화된 배열
        """
        if min_val is None:
            min_val = np.min(feature)
        if max_val is None:
            max_val = np.max(feature)

        if max_val - min_val == 0:
            return np.zeros_like(feature)

        return (feature - min_val) / (max_val - min_val)

    def smooth_feature(self, feature: np.ndarray, window_size: int = 5) -> np.ndarray:
        """
        특성을 부드럽게 만들기 (이동 평균)

        Args:
            feature: 특성 배열
            window_size: 윈도우 크기

        Returns:
            부드러워진 배열
        """
        if len(feature) < window_size:
            return feature

        kernel = np.ones(window_size) / window_size
        return np.convolve(feature, kernel, mode="same")

    def interpolate_feature(
        self,
        feature: np.ndarray,
        target_length: int
    ) -> np.ndarray:
        """
        특성을 목표 길이로 보간

        Args:
            feature: 특성 배열
            target_length: 목표 길이

        Returns:
            보간된 배열
        """
        old_indices = np.linspace(0, len(feature) - 1, len(feature))
        new_indices = np.linspace(0, len(feature) - 1, target_length)
        return np.interp(new_indices, old_indices, feature)

    def get_audio_reactive_value(
        self,
        result: AnalysisResult,
        feature_name: str,
        frame_index: int = None,
        smoothing: bool = True
    ) -> float:
        """
        오디오 반응형 값 가져오기

        Args:
            result: 분석 결과
            feature_name: 특성 이름
            frame_index: 프레임 인덱스 (None이면 평균)
            smoothing: 부드럽게 처리 여부

        Returns:
            반응형 값 (0.0 ~ 1.0)
        """
        # 특성 가져오기
        if feature_name == "tempo":
            value = result.rhythm.get("tempo", 120)
            return np.clip(value / 180, 0.0, 1.0)

        elif feature_name == "energy":
            rms = result.timbre.get("rms_energy")
            if rms is not None:
                if smoothing:
                    rms = self.smooth_feature(rms)

                if frame_index is not None and frame_index < len(rms):
                    return float(rms[frame_index])
                else:
                    return float(np.mean(rms))

        elif feature_name == "centroid":
            centroid = result.spectral.get("spectral_centroid")
            if centroid is not None:
                if smoothing:
                    centroid = self.smooth_feature(centroid)

                normalized = self.normalize_feature(centroid, 0, 8000)

                if frame_index is not None and frame_index < len(normalized):
                    return float(normalized[frame_index])
                else:
                    return float(np.mean(normalized))

        elif feature_name == "brightness":
            rolloff = result.spectral.get("spectral_rolloff")
            if rolloff is not None:
                if smoothing:
                    rolloff = self.smooth_feature(rolloff)

                normalized = self.normalize_feature(rolloff)

                if frame_index is not None and frame_index < len(normalized):
                    return float(normalized[frame_index])
                else:
                    return float(np.mean(normalized))

        # 기본값
        return 0.5
