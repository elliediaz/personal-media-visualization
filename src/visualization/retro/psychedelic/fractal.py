"""
프랙탈 시각화

Mandelbrot/Julia 프랙탈 기반 오디오 반응형 시각화
"""

import numpy as np
from numba import jit, prange
import matplotlib.pyplot as plt

from src.analysis.result import AnalysisResult
from src.visualization.artistic.base_artistic import BaseArtisticVisualizer
from src.visualization.retro.color_palettes import RetroPalettes
from src.utils.logging import get_logger

logger = get_logger(__name__)


@jit(nopython=True, parallel=True)
def compute_mandelbrot(
    x_min: float, x_max: float,
    y_min: float, y_max: float,
    width: int, height: int,
    max_iter: int
) -> np.ndarray:
    """
    Mandelbrot 집합 계산 (Numba 최적화)

    Args:
        x_min, x_max: x축 범위
        y_min, y_max: y축 범위
        width, height: 이미지 크기
        max_iter: 최대 반복 횟수

    Returns:
        이터레이션 카운트 배열
    """
    result = np.zeros((height, width), dtype=np.float64)

    for py in prange(height):
        for px in range(width):
            x0 = x_min + (x_max - x_min) * px / width
            y0 = y_min + (y_max - y_min) * py / height

            x, y = 0.0, 0.0
            iteration = 0

            while x*x + y*y <= 4 and iteration < max_iter:
                x_new = x*x - y*y + x0
                y = 2*x*y + y0
                x = x_new
                iteration += 1

            if iteration < max_iter:
                log_zn = np.log(x*x + y*y) / 2
                nu = np.log(log_zn / np.log(2)) / np.log(2)
                result[py, px] = iteration + 1 - nu
            else:
                result[py, px] = max_iter

    return result


@jit(nopython=True, parallel=True)
def compute_julia(
    c_real: float, c_imag: float,
    x_min: float, x_max: float,
    y_min: float, y_max: float,
    width: int, height: int,
    max_iter: int
) -> np.ndarray:
    """
    Julia 집합 계산 (Numba 최적화)

    Args:
        c_real, c_imag: Julia 상수의 실수/허수 부분
        x_min, x_max: x축 범위
        y_min, y_max: y축 범위
        width, height: 이미지 크기
        max_iter: 최대 반복 횟수

    Returns:
        이터레이션 카운트 배열
    """
    result = np.zeros((height, width), dtype=np.float64)

    for py in prange(height):
        for px in range(width):
            x = x_min + (x_max - x_min) * px / width
            y = y_min + (y_max - y_min) * py / height

            iteration = 0

            while x*x + y*y <= 4 and iteration < max_iter:
                x_new = x*x - y*y + c_real
                y = 2*x*y + c_imag
                x = x_new
                iteration += 1

            if iteration < max_iter:
                log_zn = np.log(x*x + y*y) / 2
                nu = np.log(log_zn / np.log(2)) / np.log(2)
                result[py, px] = iteration + 1 - nu
            else:
                result[py, px] = max_iter

    return result


class FractalVisualizer(BaseArtisticVisualizer):
    """
    프랙탈 시각화

    오디오 특성에 따라 프랙탈 파라미터가 변화하는 시각화
    """

    # 흥미로운 Julia 상수 프리셋
    JULIA_PRESETS = [
        (-0.7, 0.27015),      # Classic
        (-0.4, 0.6),          # Dendrite
        (0.285, 0.01),        # Spiral
        (-0.8, 0.156),        # Galaxy
        (-0.70176, -0.3842),  # Snowflake
        (0.355, 0.355),       # Flower
        (-0.1, 0.651),        # Rabbit
        (-0.75, 0.11),        # Double spiral
    ]

    def __init__(self, config_override: dict = None):
        """
        FractalVisualizer 초기화

        Args:
            config_override: 설정 오버라이드
        """
        super().__init__(config_override)
        self.palette = RetroPalettes.get_palette("neon")

    def render(
        self,
        result: AnalysisResult,
        fractal_type: str = "julia",
        resolution: int = 800,
        max_iter: int = 256,
        zoom: float = 1.0,
        center: tuple = (0.0, 0.0),
        **kwargs
    ):
        """
        프랙탈 시각화 렌더링

        Args:
            result: 분석 결과
            fractal_type: 프랙탈 타입 ("mandelbrot" 또는 "julia")
            resolution: 해상도
            max_iter: 최대 이터레이션
            zoom: 줌 레벨
            center: 중심 좌표
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        self.create_figure()

        # 오디오 반응형 파라미터
        energy = self.get_audio_reactive_value(result, "energy")
        centroid = self.get_audio_reactive_value(result, "centroid")
        brightness = self.get_audio_reactive_value(result, "brightness")

        # 이터레이션 조절 (에너지가 높을수록 더 상세)
        adjusted_max_iter = int(max_iter * (0.5 + energy))

        # 줌 조절 (밝기가 높을수록 확대)
        adjusted_zoom = zoom * (1.0 + brightness * 2)

        # 뷰포트 계산
        aspect = 1.0
        x_range = 3.0 / adjusted_zoom
        y_range = x_range / aspect

        x_min = center[0] - x_range / 2
        x_max = center[0] + x_range / 2
        y_min = center[1] - y_range / 2
        y_max = center[1] + y_range / 2

        # 프랙탈 계산
        if fractal_type == "mandelbrot":
            fractal_data = compute_mandelbrot(
                x_min, x_max, y_min, y_max,
                resolution, resolution,
                adjusted_max_iter
            )
        else:
            # Julia 상수 선택 (centroid 기반)
            preset_index = int(centroid * (len(self.JULIA_PRESETS) - 1))
            c_real, c_imag = self.JULIA_PRESETS[preset_index]

            # 에너지에 따른 미세 조정
            c_real += (energy - 0.5) * 0.1
            c_imag += (brightness - 0.5) * 0.05

            fractal_data = compute_julia(
                c_real, c_imag,
                x_min, x_max, y_min, y_max,
                resolution, resolution,
                adjusted_max_iter
            )

        # 정규화
        fractal_data = fractal_data / adjusted_max_iter

        # 색상맵 선택 (팔레트 기반)
        palette_name = kwargs.get("palette", "neon")
        if palette_name in ["c64", "ega", "vga"]:
            cmap = self._create_palette_colormap(palette_name)
        else:
            cmap = kwargs.get("cmap", "hot")

        # 이미지 표시
        im = self.ax.imshow(
            fractal_data,
            extent=[x_min, x_max, y_min, y_max],
            cmap=cmap,
            origin='lower',
            interpolation='bilinear'
        )

        # 축 설정
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        # 제목
        tempo = result.rhythm.get("tempo", 120)
        if fractal_type == "julia":
            preset_index = int(centroid * (len(self.JULIA_PRESETS) - 1))
            c_real, c_imag = self.JULIA_PRESETS[preset_index]
            self.set_title(f"Julia Set (c={c_real:.3f}+{c_imag:.3f}i) - {tempo:.0f} BPM")
        else:
            self.set_title(f"Mandelbrot Set - {tempo:.0f} BPM")

        logger.info(f"프랙탈 시각화 완료: {fractal_type}, {resolution}x{resolution}")
        return self.fig

    def _create_palette_colormap(self, palette_name: str):
        """
        레트로 팔레트 기반 컬러맵 생성

        Args:
            palette_name: 팔레트 이름

        Returns:
            matplotlib 컬러맵
        """
        from matplotlib.colors import LinearSegmentedColormap

        palette = RetroPalettes.get_palette(palette_name)
        colors = [(r/255, g/255, b/255) for r, g, b in palette[:16]]

        return LinearSegmentedColormap.from_list(
            f"retro_{palette_name}",
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
        # 시간 진행에 따른 줌 및 회전
        t = frame_index / total_frames
        zoom = 1.0 + t * 10  # 점진적 확대
        angle = t * np.pi * 2  # 회전

        # 중심 이동 (나선형 경로)
        center_x = -0.5 + 0.1 * np.cos(angle * 3) * t
        center_y = 0.1 * np.sin(angle * 2) * t

        return self.render(
            result,
            zoom=zoom,
            center=(center_x, center_y),
            **kwargs
        )
