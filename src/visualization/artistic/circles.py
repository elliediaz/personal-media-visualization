"""
동심원 시각화

오디오 반응형 동심원 패턴
"""

from matplotlib.patches import Circle

from src.analysis.result import AnalysisResult
from src.utils.logging import get_logger
from src.visualization.artistic.base_artistic import BaseArtisticVisualizer

logger = get_logger(__name__)


class CircleVisualizer(BaseArtisticVisualizer):
    """동심원 패턴 시각화"""

    def render(self, result: AnalysisResult, num_circles: int = 50, **kwargs):
        """
        동심원 시각화 렌더링

        Args:
            result: 분석 결과
            num_circles: 원의 개수
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        self.create_figure()

        # 비트 기반 원 생성
        beat_times = result.rhythm.get("beat_times")

        if beat_times is not None and len(beat_times) > 0:
            # 비트 시간을 반지름으로 변환
            duration = result.duration
            radii = (beat_times / duration) * 2.0

            # 원 그리기
            for i, radius in enumerate(radii[:num_circles]):
                # 색상 (템포 기반)
                tempo = result.rhythm.get("tempo", 120)
                hue = self.color_mapper.tempo_to_hue(tempo)

                # 진행에 따라 색상 변화
                color_offset = i / len(radii)
                final_hue = (hue + color_offset * 0.3) % 1.0
                color = self.color_mapper.hsv_to_rgb(final_hue, 0.7, 0.9)

                # 투명도
                alpha = 1.0 - (i / num_circles) * 0.8

                # 원 그리기
                circle = Circle(
                    (0, 0),
                    radius,
                    fill=False,
                    edgecolor=color,
                    linewidth=2,
                    alpha=alpha
                )
                self.ax.add_patch(circle)

        else:
            # 비트 정보가 없으면 균등한 간격
            for i in range(num_circles):
                radius = (i + 1) * 0.05
                alpha = 1.0 - (i / num_circles) * 0.7
                circle = Circle(
                    (0, 0),
                    radius,
                    fill=False,
                    edgecolor=self.primary_color,
                    linewidth=2,
                    alpha=alpha
                )
                self.ax.add_patch(circle)

        # 축 설정
        self.ax.set_xlim(-2.5, 2.5)
        self.ax.set_ylim(-2.5, 2.5)
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        # 제목
        self.set_title("Concentric Circles - Beat Visualization")

        logger.info(f"동심원 시각화 완료: {num_circles}개")
        return self.fig
