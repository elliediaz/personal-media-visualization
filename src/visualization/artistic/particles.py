"""
파티클 시각화

오디오 반응형 파티클 시스템
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from src.analysis.result import AnalysisResult
from src.visualization.artistic.base_artistic import BaseArtisticVisualizer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ParticleVisualizer(BaseArtisticVisualizer):
    """파티클 시스템 시각화"""

    def render(self, result: AnalysisResult, num_particles: int = 1000, **kwargs):
        """
        파티클 시각화 렌더링

        Args:
            result: 분석 결과
            num_particles: 파티클 수
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        self.create_figure()

        # 파티클 위치 생성
        np.random.seed(42)

        # 중심에서 방사형으로 파티클 배치
        angles = np.random.uniform(0, 2 * np.pi, num_particles)
        distances = np.random.exponential(0.3, num_particles)

        x = distances * np.cos(angles)
        y = distances * np.sin(angles)

        # 오디오 반응형 크기
        energy_values = result.timbre.get("rms_energy")
        if energy_values is not None:
            # 파티클마다 랜덤하게 에너지 프레임 할당
            frame_indices = np.random.randint(0, len(energy_values), num_particles)
            sizes = energy_values[frame_indices] * 500 + 10
        else:
            sizes = np.random.uniform(10, 100, num_particles)

        # 색상 (Spectral centroid 기반)
        colors = []
        centroid_values = result.spectral.get("spectral_centroid")

        if centroid_values is not None:
            frame_indices = np.random.randint(0, len(centroid_values), num_particles)
            for idx in frame_indices:
                color = self.color_mapper.spectral_centroid_to_color(centroid_values[idx])
                colors.append(color)
        else:
            colors = [(0.5, 0.8, 0.9, 0.6) for _ in range(num_particles)]

        # 파티클 그리기
        self.ax.scatter(x, y, s=sizes, c=colors, alpha=0.6, edgecolors='none')

        # 축 설정
        self.ax.set_xlim(-1.5, 1.5)
        self.ax.set_ylim(-1.5, 1.5)
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        # 제목
        tempo = result.rhythm.get("tempo", 0)
        key = result.harmonic.get("key", "Unknown")
        self.set_title(f"Audio Particles - {tempo:.0f} BPM, Key: {key}")

        logger.info(f"파티클 시각화 완료: {num_particles}개")
        return self.fig
