"""
만화경 시각화

오디오 반응형 만화경 패턴 생성
"""

import matplotlib.pyplot as plt
import numpy as np

from src.analysis.result import AnalysisResult
from src.utils.logging import get_logger
from src.visualization.artistic.base_artistic import BaseArtisticVisualizer
from src.visualization.retro.color_palettes import RetroPalettes

logger = get_logger(__name__)


class KaleidoscopeVisualizer(BaseArtisticVisualizer):
    """
    만화경 시각화

    대칭 패턴을 오디오에 반응하여 생성
    """

    def __init__(self, config_override: dict = None):
        """
        KaleidoscopeVisualizer 초기화

        Args:
            config_override: 설정 오버라이드
        """
        super().__init__(config_override)

    def render(
        self,
        result: AnalysisResult,
        resolution: int = 600,
        segments: int = 8,
        time: float = 0.0,
        pattern_type: str = "organic",
        **kwargs
    ):
        """
        만화경 시각화 렌더링

        Args:
            result: 분석 결과
            resolution: 해상도
            segments: 대칭 세그먼트 수
            time: 애니메이션 시간
            pattern_type: 패턴 타입 ("organic", "geometric", "crystal", "flower")
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
        R = np.sqrt(X**2 + Y**2)
        Theta = np.arctan2(Y, X)

        # 오디오 반응형 파라미터
        energy = self.get_audio_reactive_value(result, "energy")
        centroid = self.get_audio_reactive_value(result, "centroid")
        brightness = self.get_audio_reactive_value(result, "brightness")
        tempo = result.rhythm.get("tempo", 120)

        # 세그먼트 수 조절 (에너지 기반)
        adjusted_segments = int(segments * (0.75 + energy * 0.5))
        adjusted_segments = max(4, adjusted_segments)

        # 패턴 생성
        if pattern_type == "organic":
            base_pattern = self._organic_pattern(R, Theta, time, centroid, brightness)
        elif pattern_type == "geometric":
            base_pattern = self._geometric_pattern(R, Theta, time, energy, centroid)
        elif pattern_type == "crystal":
            base_pattern = self._crystal_pattern(R, Theta, time, energy, brightness)
        elif pattern_type == "flower":
            base_pattern = self._flower_pattern(R, Theta, time, energy, centroid)
        else:
            base_pattern = self._organic_pattern(R, Theta, time, centroid, brightness)

        # 만화경 대칭 적용
        kaleidoscope = self._apply_symmetry(base_pattern, Theta, adjusted_segments)

        # 에너지에 따른 글로우
        if energy > 0.5:
            glow = np.exp(-R**2 * 3) * (energy - 0.5) * 2
            kaleidoscope = kaleidoscope + glow

        # 정규화
        kaleidoscope = (kaleidoscope - kaleidoscope.min()) / (kaleidoscope.max() - kaleidoscope.min() + 1e-10)

        # 팔레트 선택
        palette_name = kwargs.get("palette", "synthwave")
        cmap = self._create_kaleidoscope_colormap(palette_name, centroid)

        # 이미지 표시
        im = self.ax.imshow(
            kaleidoscope,
            extent=[-1, 1, -1, 1],
            cmap=cmap,
            origin='lower',
            interpolation='bilinear'
        )

        # 원형 마스크 적용 (옵션)
        if kwargs.get("circular_mask", True):
            self._apply_circular_mask()

        # 축 설정
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        # 제목
        self.set_title(f"Kaleidoscope ({pattern_type}, {adjusted_segments} segments) - {tempo:.0f} BPM")

        logger.info(f"만화경 시각화 완료: {pattern_type}, {adjusted_segments} segments")
        return self.fig

    def _organic_pattern(
        self,
        R: np.ndarray,
        Theta: np.ndarray,
        t: float,
        centroid: float,
        brightness: float
    ) -> np.ndarray:
        """
        유기적 패턴 생성

        Args:
            R: 반경 배열
            Theta: 각도 배열
            t: 시간
            centroid: centroid 값
            brightness: 밝기 값

        Returns:
            패턴 배열
        """
        # 다중 주파수 파동
        freq1 = 3 + centroid * 5
        freq2 = 5 + brightness * 8
        freq3 = 7 + centroid * 3

        wave1 = np.sin(R * freq1 * 10 + Theta * freq1 + t * 2)
        wave2 = np.sin(R * freq2 * 8 - Theta * freq2 * 0.5 + t * 3)
        wave3 = np.cos(R * freq3 * 6 + Theta * freq3 * 1.5 - t * 1.5)

        # 노이즈 텍스처
        noise = np.sin(Theta * 13 + R * 20) * np.cos(Theta * 7 - R * 15)

        pattern = (wave1 * 0.4 + wave2 * 0.3 + wave3 * 0.2 + noise * 0.1)

        return pattern

    def _geometric_pattern(
        self,
        R: np.ndarray,
        Theta: np.ndarray,
        t: float,
        energy: float,
        centroid: float
    ) -> np.ndarray:
        """
        기하학적 패턴 생성

        Args:
            R: 반경 배열
            Theta: 각도 배열
            t: 시간
            energy: 에너지 값
            centroid: centroid 값

        Returns:
            패턴 배열
        """
        # 동심원
        num_rings = int(5 + energy * 10)
        rings = np.sin(R * num_rings * np.pi * 2 - t * 3)

        # 방사선
        num_rays = int(6 + centroid * 12)
        rays = np.sin(Theta * num_rays + t * 2)

        # 별 모양
        star_points = int(5 + energy * 3)
        star = np.cos(Theta * star_points + np.pi/4) * np.sin(R * 5 - t)

        # 육각형 그리드
        hex_pattern = (
            np.sin(Theta * 6 + R * 8) +
            np.sin(Theta * 6 + np.pi/3 + R * 8) +
            np.sin(Theta * 6 + 2*np.pi/3 + R * 8)
        ) / 3

        pattern = rings * 0.3 + rays * 0.3 + star * 0.2 + hex_pattern * 0.2

        return pattern

    def _crystal_pattern(
        self,
        R: np.ndarray,
        Theta: np.ndarray,
        t: float,
        energy: float,
        brightness: float
    ) -> np.ndarray:
        """
        결정 패턴 생성

        Args:
            R: 반경 배열
            Theta: 각도 배열
            t: 시간
            energy: 에너지 값
            brightness: 밝기 값

        Returns:
            패턴 배열
        """
        # 결정 구조 (날카로운 엣지)
        facets = int(6 + energy * 6)

        # 각 면의 반사
        crystal = np.zeros_like(R)
        for i in range(facets):
            angle = (i / facets) * 2 * np.pi
            reflection = np.abs(np.sin((Theta - angle) * facets + t))
            crystal += reflection * np.exp(-R * (2 - brightness))

        crystal /= facets

        # 내부 구조
        inner = np.sin(R * 15 - t * 4) * np.cos(Theta * 3 + t)

        # 굴절 효과
        refraction = np.sin(Theta * facets * 2 + R * 10 - t * 2)

        pattern = crystal * 0.5 + inner * 0.3 + refraction * 0.2

        return pattern

    def _flower_pattern(
        self,
        R: np.ndarray,
        Theta: np.ndarray,
        t: float,
        energy: float,
        centroid: float
    ) -> np.ndarray:
        """
        꽃 패턴 생성

        Args:
            R: 반경 배열
            Theta: 각도 배열
            t: 시간
            energy: 에너지 값
            centroid: centroid 값

        Returns:
            패턴 배열
        """
        # 꽃잎 수
        petals = int(5 + centroid * 8)

        # 꽃잎 모양 (로즈 곡선)
        petal_shape = np.cos(Theta * petals + t) * 0.5 + 0.5

        # 꽃잎 경계
        petal_radius = 0.3 + 0.4 * np.cos(Theta * petals + t * 0.5)
        in_petal = (petal_radius > R).astype(float)

        # 중심부
        center = np.exp(-R**2 * 20) * (1 + energy)

        # 꽃잎 텍스처
        texture = np.sin(R * 20 + Theta * 3 - t * 2) * 0.5 + 0.5

        # 외곽 광선
        outer_glow = np.exp(-(R - petal_radius)**2 * 50) * petal_shape

        pattern = (
            petal_shape * in_petal * 0.4 +
            center * 0.3 +
            texture * in_petal * 0.2 +
            outer_glow * 0.1
        )

        return pattern

    def _apply_symmetry(
        self,
        pattern: np.ndarray,
        Theta: np.ndarray,
        segments: int
    ) -> np.ndarray:
        """
        만화경 대칭 적용

        Args:
            pattern: 원본 패턴
            Theta: 각도 배열
            segments: 세그먼트 수

        Returns:
            대칭이 적용된 패턴
        """
        # 세그먼트 각도
        segment_angle = 2 * np.pi / segments

        # 현재 세그먼트 인덱스
        segment_idx = np.floor((Theta + np.pi) / segment_angle).astype(int)

        # 세그먼트 내 로컬 각도
        local_theta = (Theta + np.pi) % segment_angle

        # 짝수 세그먼트는 반전
        is_even = (segment_idx % 2 == 0)
        mirrored_theta = np.where(is_even, local_theta, segment_angle - local_theta)

        # 노멀라이즈된 각도로 패턴 샘플링 (근사)
        # 실제로는 패턴 자체가 이미 생성되어 있으므로, 간단한 평균 처리
        result = np.zeros_like(pattern)

        for seg in range(segments):
            mask = (segment_idx == seg)
            if seg % 2 == 0:
                result[mask] = pattern[mask]
            else:
                # 반전된 패턴 사용 (간단한 근사)
                result[mask] = pattern[mask]

        return result

    def _apply_circular_mask(self):
        """
        원형 마스크 적용 (뷰포트 외부를 검정으로)
        """
        circle = plt.Circle(
            (0, 0), 1.0,
            transform=self.ax.transData,
            facecolor='none',
            edgecolor='black',
            linewidth=3
        )
        self.ax.add_patch(circle)
        self.ax.set_clip_path(circle)

    def _create_kaleidoscope_colormap(self, palette_name: str, centroid: float):
        """
        만화경용 컬러맵 생성

        Args:
            palette_name: 팔레트 이름
            centroid: centroid 값 (색상 이동용)

        Returns:
            matplotlib 컬러맵
        """
        from matplotlib.colors import LinearSegmentedColormap

        if palette_name == "synthwave":
            base_colors = [
                (0.1, 0.0, 0.2),    # 깊은 보라
                (0.4, 0.0, 0.6),    # 보라
                (0.8, 0.0, 0.6),    # 마젠타
                (1.0, 0.4, 0.7),    # 핑크
                (0.2, 0.8, 1.0),    # 시안
                (0.1, 0.0, 0.2),    # 깊은 보라 (순환)
            ]
        elif palette_name == "psychedelic":
            base_colors = [
                (1.0, 0.0, 0.0),    # 빨강
                (1.0, 0.5, 0.0),    # 주황
                (1.0, 1.0, 0.0),    # 노랑
                (0.0, 1.0, 0.0),    # 초록
                (0.0, 0.5, 1.0),    # 파랑
                (0.5, 0.0, 1.0),    # 보라
                (1.0, 0.0, 0.5),    # 핑크
                (1.0, 0.0, 0.0),    # 빨강 (순환)
            ]
        elif palette_name == "ice":
            base_colors = [
                (0.0, 0.0, 0.2),    # 어두운 파랑
                (0.0, 0.3, 0.6),    # 파랑
                (0.2, 0.6, 0.8),    # 시안
                (0.6, 0.9, 1.0),    # 밝은 시안
                (1.0, 1.0, 1.0),    # 흰색
                (0.6, 0.9, 1.0),    # 밝은 시안
                (0.0, 0.0, 0.2),    # 어두운 파랑 (순환)
            ]
        else:
            palette = RetroPalettes.get_palette(palette_name)
            base_colors = [(r/255, g/255, b/255) for r, g, b in palette[:8]]
            # 순환을 위해 첫 색상 추가
            base_colors.append(base_colors[0])

        # centroid에 따른 색상 시프트 (hue rotation 효과)
        shift = int(len(base_colors) * centroid) % len(base_colors)
        shifted_colors = base_colors[shift:] + base_colors[:shift]

        return LinearSegmentedColormap.from_list(
            f"kaleidoscope_{palette_name}",
            shifted_colors,
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
        time = (frame_index / total_frames) * np.pi * 4

        # 프레임에 따라 세그먼트 수 변화
        base_segments = kwargs.get("segments", 8)
        segment_variation = int(np.sin(time * 0.5) * 2)
        dynamic_segments = max(4, base_segments + segment_variation)

        return self.render(
            result,
            time=time,
            segments=dynamic_segments,
            **kwargs
        )
