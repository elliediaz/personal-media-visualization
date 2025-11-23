"""
예술적 시각화 기본 클래스

오디오 반응형 예술적 시각화를 위한 기본 클래스
"""

import numpy as np
from pathlib import Path

from src.analysis.result import AnalysisResult
from src.visualization.artistic.color_mapping import ColorMapper
from src.visualization.base import BaseVisualizer
from src.utils.logging import get_logger

logger = get_logger(__name__)


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
