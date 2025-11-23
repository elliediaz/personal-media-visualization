"""
파동 간섭 시각화

오디오 반응형 파동 간섭 패턴
"""

import numpy as np
import matplotlib.pyplot as plt

from src.analysis.result import AnalysisResult
from src.visualization.artistic.base_artistic import BaseArtisticVisualizer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class WaveInterferenceVisualizer(BaseArtisticVisualizer):
    """파동 간섭 패턴 시각화"""

    def render(self, result: AnalysisResult, resolution: int = 500, **kwargs):
        """
        파동 간섭 시각화 렌더링

        Args:
            result: 분석 결과
            resolution: 해상도
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        self.create_figure()

        # 그리드 생성
        x = np.linspace(-2, 2, resolution)
        y = np.linspace(-2, 2, resolution)
        X, Y = np.meshgrid(x, y)

        # 파동 소스 위치 (onset 기반)
        onset_times = result.rhythm.get("onset_times")

        if onset_times is not None and len(onset_times) > 0:
            # 처음 몇 개의 onset 사용
            num_sources = min(8, len(onset_times))
            sources = []

            for i in range(num_sources):
                # onset 시간을 각도로 변환
                angle = (onset_times[i] / result.duration) * 2 * np.pi
                radius = 1.0

                x_pos = radius * np.cos(angle)
                y_pos = radius * np.sin(angle)
                sources.append((x_pos, y_pos))

        else:
            # 기본 소스 (원형 배치)
            num_sources = 6
            sources = []
            for i in range(num_sources):
                angle = i * (2 * np.pi / num_sources)
                sources.append((np.cos(angle), np.sin(angle)))

        # 파동 계산
        Z = np.zeros_like(X)

        # 템포에 따른 주파수
        tempo = result.rhythm.get("tempo", 120)
        frequency = tempo / 60.0  # Hz

        for i, (sx, sy) in enumerate(sources):
            # 각 소스로부터의 거리
            distance = np.sqrt((X - sx)**2 + (Y - sy)**2)

            # 파동 (감쇠 포함)
            wave = np.sin(distance * 10 * frequency) * np.exp(-distance * 0.5)

            # Spectral centroid에 따른 위상 변화
            centroid = result.spectral.get("spectral_centroid")
            if centroid is not None:
                phase = (i / num_sources) * np.mean(centroid) / 1000
            else:
                phase = i / num_sources

            Z += wave * np.cos(phase * np.pi)

        # 정규화
        Z = Z / np.max(np.abs(Z))

        # 색상맵
        cmap = kwargs.get("cmap", "twilight")

        # 이미지 표시
        im = self.ax.imshow(
            Z,
            extent=[-2, 2, -2, 2],
            cmap=cmap,
            origin='lower',
            interpolation='bilinear',
            alpha=0.9
        )

        # 소스 위치 표시
        for sx, sy in sources:
            self.ax.plot(sx, sy, 'o', color='white', markersize=8, alpha=0.8)

        # 컬러바
        cbar = plt.colorbar(im, ax=self.ax)
        cbar.ax.yaxis.set_tick_params(color=self.fg_color)
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=self.fg_color)

        # 축 설정
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        # 제목
        self.set_title(f"Wave Interference - {tempo:.0f} BPM")

        logger.info(f"파동 간섭 시각화 완료: {num_sources}개 소스")
        return self.fig
