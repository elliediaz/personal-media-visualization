"""
특성 타임라인 시각화

오디오 특성의 시간에 따른 변화를 시각화합니다.
"""

import librosa
import numpy as np

from src.analysis.result import AnalysisResult
from src.visualization.base import BaseVisualizer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class FeatureVisualizer(BaseVisualizer):
    """특성 타임라인 시각화기"""

    def render(self, result: AnalysisResult = None, features: list = None, **kwargs):
        """
        특성 타임라인 렌더링

        Args:
            result: 분석 결과
            features: 표시할 특성 리스트 (예: ["spectral_centroid", "rms_energy"])
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        if result is None:
            raise ValueError("분석 결과가 필요합니다")

        if features is None:
            # 기본 특성
            features = ["spectral_centroid", "rms_energy", "zero_crossing_rate"]

        # Figure 생성
        import matplotlib.pyplot as plt
        num_features = len(features)
        fig, axes = plt.subplots(num_features, 1, figsize=(12, 3 * num_features), dpi=self.dpi)

        if num_features == 1:
            axes = [axes]

        # 각 특성 그리기
        for i, feature_name in enumerate(features):
            ax = axes[i]

            # 특성 데이터 가져오기
            feature_data = self._get_feature_data(result, feature_name)

            if feature_data is None:
                logger.warning(f"특성을 찾을 수 없음: {feature_name}")
                continue

            # 시간 축 생성
            times = librosa.frames_to_time(
                np.arange(len(feature_data)), sr=result.sample_rate
            )

            # 그래프 그리기
            ax.plot(times, feature_data, color=self.primary_color, linewidth=1.5)
            ax.fill_between(times, feature_data, alpha=0.3, color=self.primary_color)

            # 스타일 설정
            ax.set_facecolor(self.bg_color)
            ax.set_title(self._get_feature_title(feature_name), color=self.fg_color)
            ax.set_xlabel("시간 (초)", color=self.fg_color)
            ax.set_ylabel(self._get_feature_unit(feature_name), color=self.fg_color)
            ax.tick_params(colors=self.fg_color)
            ax.grid(True, alpha=0.3, linestyle="--", color=self.fg_color)

            # 축 색상
            for spine in ax.spines.values():
                spine.set_color(self.fg_color)

        plt.tight_layout()
        self.fig = fig

        logger.info(f"{len(features)}개 특성 렌더링 완료")
        return self.fig

    def _get_feature_data(self, result: AnalysisResult, feature_name: str) -> np.ndarray:
        """특성 데이터 가져오기"""
        # Spectral features
        if feature_name == "spectral_centroid":
            return result.spectral.get("spectral_centroid")
        elif feature_name == "spectral_rolloff":
            return result.spectral.get("spectral_rolloff")
        elif feature_name == "spectral_bandwidth":
            return result.spectral.get("spectral_bandwidth")
        elif feature_name == "zero_crossing_rate":
            return result.spectral.get("zero_crossing_rate")
        elif feature_name == "spectral_flatness":
            return result.spectral.get("spectral_flatness")

        # Timbre features
        elif feature_name == "rms_energy":
            return result.timbre.get("rms_energy")

        # Rhythm features
        elif feature_name == "onset_strength":
            return result.rhythm.get("onset_strength")

        return None

    def _get_feature_title(self, feature_name: str) -> str:
        """특성 제목 반환"""
        titles = {
            "spectral_centroid": "Spectral Centroid (스펙트럼 중심)",
            "spectral_rolloff": "Spectral Rolloff",
            "spectral_bandwidth": "Spectral Bandwidth",
            "zero_crossing_rate": "Zero-Crossing Rate",
            "spectral_flatness": "Spectral Flatness",
            "rms_energy": "RMS Energy (에너지)",
            "onset_strength": "Onset Strength (음 시작점 강도)",
        }
        return titles.get(feature_name, feature_name)

    def _get_feature_unit(self, feature_name: str) -> str:
        """특성 단위 반환"""
        units = {
            "spectral_centroid": "Hz",
            "spectral_rolloff": "Hz",
            "spectral_bandwidth": "Hz",
            "zero_crossing_rate": "Rate",
            "spectral_flatness": "Flatness",
            "rms_energy": "Amplitude",
            "onset_strength": "Strength",
        }
        return units.get(feature_name, "Value")
