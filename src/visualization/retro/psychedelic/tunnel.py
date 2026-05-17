"""
터널 시각화

오디오 반응형 사이키델릭 터널/와프 효과
"""

import matplotlib.pyplot as plt
import numpy as np

from src.analysis.result import AnalysisResult
from src.utils.logging import get_logger
from src.visualization.artistic.base_artistic import BaseArtisticVisualizer
from src.visualization.retro.color_palettes import RetroPalettes

logger = get_logger(__name__)


class TunnelVisualizer(BaseArtisticVisualizer):
    """
    터널 시각화

    무한 터널 효과를 오디오에 반응하여 렌더링
    """

    def __init__(self, config_override: dict = None):
        """
        TunnelVisualizer 초기화

        Args:
            config_override: 설정 오버라이드
        """
        super().__init__(config_override)
        self.time_offset = 0.0

    def render(
        self,
        result: AnalysisResult,
        resolution: int = 600,
        tunnel_type: str = "spiral",
        time: float = 0.0,
        **kwargs
    ):
        """
        터널 시각화 렌더링

        Args:
            result: 분석 결과
            resolution: 해상도
            tunnel_type: 터널 타입 ("spiral", "warp", "vortex", "grid")
            time: 애니메이션 시간
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        self.create_figure()

        # 그리드 생성
        x = np.linspace(-1, 1, resolution)
        y = np.linspace(-1, 1, resolution)
        X, Y = np.meshgrid(x, y)

        # 극좌표 변환
        R = np.sqrt(X**2 + Y**2) + 1e-10
        Theta = np.arctan2(Y, X)

        # 오디오 반응형 파라미터
        energy = self.get_audio_reactive_value(result, "energy")
        centroid = self.get_audio_reactive_value(result, "centroid")
        brightness = self.get_audio_reactive_value(result, "brightness")
        tempo = result.rhythm.get("tempo", 120)

        # 시간 오프셋 (템포 기반)
        time_factor = tempo / 120.0
        t = time * time_factor

        # 터널 효과 계산
        if tunnel_type == "spiral":
            Z = self._spiral_tunnel(R, Theta, t, energy, centroid)
        elif tunnel_type == "warp":
            Z = self._warp_tunnel(R, Theta, t, energy, brightness)
        elif tunnel_type == "vortex":
            Z = self._vortex_tunnel(R, Theta, t, energy, centroid)
        elif tunnel_type == "grid":
            Z = self._grid_tunnel(X, Y, R, t, energy, brightness)
        else:
            Z = self._spiral_tunnel(R, Theta, t, energy, centroid)

        # 팔레트 선택
        palette_name = kwargs.get("palette", "synthwave")
        cmap = self._create_tunnel_colormap(palette_name)

        # 이미지 표시
        self.ax.imshow(
            Z,
            extent=[-1, 1, -1, 1],
            cmap=cmap,
            origin='lower',
            interpolation='bilinear'
        )

        # 중심 글로우 효과
        if kwargs.get("center_glow", True):
            self._add_center_glow(energy)

        # 축 설정
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        # 제목
        self.set_title(f"Tunnel ({tunnel_type}) - {tempo:.0f} BPM")

        logger.info(f"터널 시각화 완료: {tunnel_type}")
        return self.fig

    def _spiral_tunnel(
        self,
        R: np.ndarray,
        Theta: np.ndarray,
        t: float,
        energy: float,
        centroid: float
    ) -> np.ndarray:
        """
        나선형 터널 효과

        Args:
            R: 반경 배열
            Theta: 각도 배열
            t: 시간
            energy: 에너지 값
            centroid: centroid 값

        Returns:
            효과 배열
        """
        # 터널 깊이
        depth = 1.0 / (R + 0.1)

        # 나선 회전
        spiral_factor = 3 + centroid * 5
        rotation = Theta + depth * spiral_factor + t * 2

        # 밝기 변조
        brightness = np.sin(depth * 10 - t * 5) * 0.5 + 0.5
        pattern = np.sin(rotation * 4) * 0.5 + 0.5

        # 에너지에 따른 펄스
        pulse = 1.0 + energy * 0.5 * np.sin(t * 10)

        # 최종 조합
        Z = (brightness * pattern * pulse) * np.exp(-R * 0.5)

        return Z

    def _warp_tunnel(
        self,
        R: np.ndarray,
        Theta: np.ndarray,
        t: float,
        energy: float,
        brightness: float
    ) -> np.ndarray:
        """
        와프 터널 효과

        Args:
            R: 반경 배열
            Theta: 각도 배열
            t: 시간
            energy: 에너지 값
            brightness: 밝기 값

        Returns:
            효과 배열
        """
        # 하이퍼스페이스 와프 효과
        warp_speed = 2 + energy * 3

        # 깊이 기반 스트레치
        stretch = np.log(R + 1) * warp_speed

        # 별 스트릭 패턴
        num_streaks = int(8 + brightness * 16)
        streaks = np.zeros_like(R)

        for i in range(num_streaks):
            angle = (i / num_streaks) * 2 * np.pi
            streak = np.exp(-((Theta - angle) % (2 * np.pi / num_streaks))**2 * 50)
            streaks += streak

        # 시간에 따른 이동
        moving = np.sin(stretch - t * warp_speed) * 0.5 + 0.5

        # 중심 밝기
        center_bright = np.exp(-R**2 * 5) * (1 + energy)

        Z = (streaks * moving + center_bright) * np.exp(-R * 0.3)

        return Z

    def _vortex_tunnel(
        self,
        R: np.ndarray,
        Theta: np.ndarray,
        t: float,
        energy: float,
        centroid: float
    ) -> np.ndarray:
        """
        소용돌이 터널 효과

        Args:
            R: 반경 배열
            Theta: 각도 배열
            t: 시간
            energy: 에너지 값
            centroid: centroid 값

        Returns:
            효과 배열
        """
        # 소용돌이 회전
        vortex_strength = 5 + centroid * 10
        twisted_theta = Theta + R * vortex_strength + t * 3

        # 다중 레이어
        layer1 = np.sin(twisted_theta * 6) * np.cos(R * 20 - t * 4)
        layer2 = np.sin(twisted_theta * 3 + np.pi/3) * np.cos(R * 15 - t * 3)
        layer3 = np.sin(twisted_theta * 9 + np.pi/6) * np.cos(R * 25 - t * 5)

        # 에너지에 따른 레이어 가중치
        w1 = 0.5 + energy * 0.3
        w2 = 0.3
        w3 = 0.2 * energy

        Z = (layer1 * w1 + layer2 * w2 + layer3 * w3) * 0.5 + 0.5

        # 깊이 감쇠
        Z *= np.exp(-R * 0.5)

        return Z

    def _grid_tunnel(
        self,
        X: np.ndarray,
        Y: np.ndarray,
        R: np.ndarray,
        t: float,
        energy: float,
        brightness: float
    ) -> np.ndarray:
        """
        그리드 터널 효과 (Tron 스타일)

        Args:
            X, Y: 좌표 배열
            R: 반경 배열
            t: 시간
            energy: 에너지 값
            brightness: 밝기 값

        Returns:
            효과 배열
        """
        # 원근감 있는 그리드
        depth = 1.0 / (R + 0.1)
        grid_scale = 10 + brightness * 20

        # 그리드 라인
        grid_x = np.sin(X * grid_scale * depth + t * 2)
        grid_y = np.sin(Y * grid_scale * depth + t * 2)

        # 그리드 패턴 (얇은 라인)
        line_width = 0.1 + energy * 0.1
        grid = np.maximum(
            np.exp(-grid_x**2 / line_width),
            np.exp(-grid_y**2 / line_width)
        )

        # 펄스 링
        ring_freq = 5 + energy * 5
        rings = np.sin(R * ring_freq - t * 3) * 0.5 + 0.5

        # 조합
        Z = (grid * 0.7 + rings * 0.3) * np.exp(-R * 0.3)

        return Z

    def _add_center_glow(self, energy: float):
        """
        중심 글로우 효과 추가

        Args:
            energy: 에너지 값
        """
        # 글로우 원 추가
        glow_size = 0.1 + energy * 0.05
        circle = plt.Circle(
            (0, 0), glow_size,
            color='white',
            alpha=0.3 + energy * 0.3
        )
        self.ax.add_patch(circle)

        # 내부 코어
        core = plt.Circle(
            (0, 0), glow_size * 0.3,
            color='white',
            alpha=0.8
        )
        self.ax.add_patch(core)

    def _create_tunnel_colormap(self, palette_name: str):
        """
        터널용 컬러맵 생성

        Args:
            palette_name: 팔레트 이름

        Returns:
            matplotlib 컬러맵
        """
        from matplotlib.colors import LinearSegmentedColormap

        if palette_name == "synthwave":
            colors = [
                (0.0, 0.0, 0.1),    # 깊은 보라
                (0.3, 0.0, 0.5),    # 보라
                (0.8, 0.0, 0.5),    # 마젠타
                (1.0, 0.2, 0.6),    # 핑크
                (0.0, 1.0, 1.0),    # 시안
                (1.0, 1.0, 1.0),    # 흰색
            ]
        elif palette_name == "neon":
            colors = [
                (0.0, 0.0, 0.0),    # 검정
                (0.0, 1.0, 0.0),    # 네온 그린
                (0.0, 1.0, 1.0),    # 시안
                (1.0, 0.0, 1.0),    # 마젠타
                (1.0, 1.0, 0.0),    # 노랑
                (1.0, 1.0, 1.0),    # 흰색
            ]
        elif palette_name == "fire":
            colors = [
                (0.0, 0.0, 0.0),    # 검정
                (0.5, 0.0, 0.0),    # 어두운 빨강
                (1.0, 0.2, 0.0),    # 주황
                (1.0, 0.6, 0.0),    # 밝은 주황
                (1.0, 1.0, 0.2),    # 노랑
                (1.0, 1.0, 1.0),    # 흰색
            ]
        else:
            palette = RetroPalettes.get_palette(palette_name)
            colors = [(r/255, g/255, b/255) for r, g, b in palette[:8]]

        return LinearSegmentedColormap.from_list(
            f"tunnel_{palette_name}",
            colors,
            N=256
        )

    def render_animation_frame(
        self,
        result: AnalysisResult,
        frame_index: int,
        total_frames: int,
        **kwargs
    ):
        """
        애니메이션 프레임 렌더링

        Args:
            result: 분석 결과
            frame_index: 현재 프레임 인덱스
            total_frames: 총 프레임 수
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        time = (frame_index / total_frames) * np.pi * 4  # 2 사이클

        return self.render(
            result,
            time=time,
            **kwargs
        )
