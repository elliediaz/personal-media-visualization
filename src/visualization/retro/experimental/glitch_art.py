"""
글리치 아트 시각화

오디오 반응형 글리치 효과 생성
"""

import io

import numpy as np
from PIL import Image

from src.analysis.result import AnalysisResult
from src.utils.logging import get_logger
from src.visualization.artistic.base_artistic import BaseArtisticVisualizer

logger = get_logger(__name__)


class GlitchArtVisualizer(BaseArtisticVisualizer):
    """
    글리치 아트 시각화

    이미지나 시각화 결과에 글리치 효과를 적용
    """

    def __init__(self, config_override: dict = None):
        """
        GlitchArtVisualizer 초기화

        Args:
            config_override: 설정 오버라이드
        """
        super().__init__(config_override)

    def render(
        self,
        result: AnalysisResult,
        base_image: np.ndarray = None,
        resolution: int = 600,
        glitch_intensity: float = 0.5,
        time: float = 0.0,
        **kwargs
    ):
        """
        글리치 아트 시각화 렌더링

        Args:
            result: 분석 결과
            base_image: 기본 이미지 (없으면 노이즈 생성)
            resolution: 해상도
            glitch_intensity: 글리치 강도 (0.0-1.0)
            time: 애니메이션 시간
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        self.create_figure()

        # 오디오 반응형 파라미터
        energy = self.get_audio_reactive_value(result, "energy")
        centroid = self.get_audio_reactive_value(result, "centroid")
        self.get_audio_reactive_value(result, "brightness")

        # 기본 이미지 생성 또는 사용
        if base_image is None:
            base_image = self._generate_base_pattern(resolution, time, centroid)

        # 글리치 강도 조절 (에너지 기반)
        adjusted_intensity = glitch_intensity * (0.5 + energy)

        # 글리치 효과 적용
        glitched = base_image.copy()

        # 효과 선택 (에너지 레벨에 따라)
        if energy > 0.7:
            glitched = self._apply_heavy_glitch(glitched, adjusted_intensity, time)
        elif energy > 0.4:
            glitched = self._apply_medium_glitch(glitched, adjusted_intensity, time)
        else:
            glitched = self._apply_light_glitch(glitched, adjusted_intensity, time)

        # RGB 시프트 (centroid 기반)
        if centroid > 0.3:
            glitched = self._apply_rgb_shift(glitched, centroid * 10)

        # 스캔라인 노이즈
        if kwargs.get("scanline_noise", True):
            glitched = self._apply_scanline_noise(glitched, energy * 0.3)

        # 이미지 표시
        self.ax.imshow(glitched)
        self.ax.axis('off')

        # 제목
        tempo = result.rhythm.get("tempo", 120)
        self.set_title(f"Glitch Art - {tempo:.0f} BPM")

        logger.info(f"글리치 아트 시각화 완료: 강도 {adjusted_intensity:.2f}")
        return self.fig

    def _generate_base_pattern(
        self,
        resolution: int,
        time: float,
        centroid: float
    ) -> np.ndarray:
        """
        기본 패턴 생성

        Args:
            resolution: 해상도
            time: 시간
            centroid: centroid 값

        Returns:
            RGB 이미지 배열
        """
        x = np.linspace(0, 1, resolution)
        y = np.linspace(0, 1, resolution)
        X, Y = np.meshgrid(x, y)

        # 여러 패턴 레이어
        pattern1 = np.sin(X * 20 + time * 2) * np.cos(Y * 15 - time)
        pattern2 = np.sin((X + Y) * 10 + time * 3)
        pattern3 = np.sin(np.sqrt(X**2 + Y**2) * 30 - time * 2)

        # 조합
        combined = (pattern1 + pattern2 * 0.5 + pattern3 * 0.3) / 1.8
        combined = (combined + 1) / 2  # 0-1 범위로

        # RGB 채널 생성
        r = combined * (0.8 + centroid * 0.4)
        g = np.roll(combined, int(resolution * 0.1), axis=1) * 0.7
        b = np.roll(combined, int(resolution * 0.05), axis=0) * (0.5 + centroid * 0.5)

        # 스택
        image = np.stack([r, g, b], axis=-1)
        image = np.clip(image * 255, 0, 255).astype(np.uint8)

        return image

    def _apply_light_glitch(
        self,
        image: np.ndarray,
        intensity: float,
        time: float
    ) -> np.ndarray:
        """
        가벼운 글리치 효과

        Args:
            image: 입력 이미지
            intensity: 강도
            time: 시간

        Returns:
            글리치된 이미지
        """
        result = image.copy()
        height, width = image.shape[:2]

        # 가끔씩 수평 라인 시프트
        num_lines = int(5 * intensity)
        for _ in range(num_lines):
            y = np.random.randint(0, height)
            shift = np.random.randint(-int(20 * intensity), int(20 * intensity))
            result[y] = np.roll(result[y], shift, axis=0)

        return result

    def _apply_medium_glitch(
        self,
        image: np.ndarray,
        intensity: float,
        time: float
    ) -> np.ndarray:
        """
        중간 글리치 효과

        Args:
            image: 입력 이미지
            intensity: 강도
            time: 시간

        Returns:
            글리치된 이미지
        """
        result = self._apply_light_glitch(image, intensity, time)
        height, width = image.shape[:2]

        # 블록 글리치
        num_blocks = int(3 * intensity)
        for _ in range(num_blocks):
            block_h = np.random.randint(10, 50)
            block_w = np.random.randint(50, 200)
            y = np.random.randint(0, height - block_h)
            x = np.random.randint(0, width - block_w)

            # 블록 복사 및 이동
            block = result[y:y+block_h, x:x+block_w].copy()
            new_x = np.clip(x + np.random.randint(-50, 50), 0, width - block_w)
            result[y:y+block_h, new_x:new_x+block_w] = block

        return result

    def _apply_heavy_glitch(
        self,
        image: np.ndarray,
        intensity: float,
        time: float
    ) -> np.ndarray:
        """
        강한 글리치 효과

        Args:
            image: 입력 이미지
            intensity: 강도
            time: 시간

        Returns:
            글리치된 이미지
        """
        result = self._apply_medium_glitch(image, intensity, time)
        height, width = image.shape[:2]

        # 채널 분리 및 왜곡
        r, g, b = result[:,:,0], result[:,:,1], result[:,:,2]

        # 각 채널 다르게 왜곡
        shift_r = int(np.sin(time * 5) * 15 * intensity)
        shift_g = int(np.cos(time * 3) * 10 * intensity)

        r = np.roll(r, shift_r, axis=1)
        g = np.roll(g, shift_g, axis=0)

        result = np.stack([r, g, b], axis=-1)

        # 노이즈 오버레이
        noise = np.random.randint(0, int(50 * intensity), result.shape, dtype=np.uint8)
        result = np.clip(result.astype(np.int16) + noise - 25, 0, 255).astype(np.uint8)

        # 줄 손상
        num_corrupt = int(10 * intensity)
        for _ in range(num_corrupt):
            y = np.random.randint(0, height)
            result[y] = np.random.randint(0, 255, (width, 3), dtype=np.uint8)

        return result

    def _apply_rgb_shift(self, image: np.ndarray, shift: float) -> np.ndarray:
        """
        RGB 채널 시프트

        Args:
            image: 입력 이미지
            shift: 시프트 양

        Returns:
            시프트된 이미지
        """
        r, g, b = image[:,:,0], image[:,:,1], image[:,:,2]

        shift_amount = int(shift)
        r = np.roll(r, shift_amount, axis=1)
        b = np.roll(b, -shift_amount, axis=1)

        return np.stack([r, g, b], axis=-1)

    def _apply_scanline_noise(
        self,
        image: np.ndarray,
        intensity: float
    ) -> np.ndarray:
        """
        스캔라인 노이즈 적용

        Args:
            image: 입력 이미지
            intensity: 강도

        Returns:
            노이즈가 적용된 이미지
        """
        result = image.copy().astype(np.float32)
        height = image.shape[0]

        # 랜덤 스캔라인에 노이즈
        for y in range(0, height, 2):
            if np.random.random() < intensity:
                noise_level = np.random.random() * 0.3
                result[y] = result[y] * (1 - noise_level) + 128 * noise_level

        return np.clip(result, 0, 255).astype(np.uint8)

    def apply_to_figure(self, fig, intensity: float = 0.5) -> np.ndarray:
        """
        기존 Figure에 글리치 효과 적용

        Args:
            fig: matplotlib Figure
            intensity: 강도

        Returns:
            글리치된 이미지 배열
        """
        # Figure를 이미지로 변환
        buf = io.BytesIO()
        fig.savefig(buf, format='png', facecolor=fig.get_facecolor())
        buf.seek(0)

        image = Image.open(buf)
        image_array = np.array(image)[:, :, :3]  # RGB만

        # 글리치 적용
        glitched = self._apply_medium_glitch(image_array, intensity, 0)
        glitched = self._apply_rgb_shift(glitched, intensity * 5)

        return glitched

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

        return self.render(
            result,
            time=time,
            **kwargs
        )
