"""
정적 노이즈 및 글리치 효과

아날로그 신호 간섭과 글리치를 시뮬레이션합니다.
"""

import numpy as np

from .base_effect import BaseEffect


class NoiseEffect(BaseEffect):
    """
    정적 노이즈 효과

    아날로그 TV의 정적 노이즈를 재현합니다.
    """

    def __init__(
        self,
        enabled: bool = True,
        intensity: float = 0.05,
        monochrome: bool = True,
        animated: bool = True,
        seed: int = None,
    ):
        """
        노이즈 효과 초기화

        Args:
            enabled: 효과 활성화 여부
            intensity: 노이즈 강도 (0.0 ~ 1.0)
            monochrome: 흑백 노이즈 여부
            animated: 매 프레임 다른 노이즈 생성
            seed: 랜덤 시드 (None이면 매번 다른 노이즈)
        """
        super().__init__(enabled, intensity)
        self.monochrome = monochrome
        self.animated = animated
        self.seed = seed
        self._rng = np.random.default_rng(seed)

    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        노이즈 효과 적용

        Args:
            image: 입력 이미지 (H, W, C)

        Returns:
            노이즈가 적용된 이미지
        """
        if not self.enabled or self.intensity == 0:
            return image

        is_uint8 = image.dtype == np.uint8
        img = self._ensure_float(image)
        height, width = img.shape[:2]

        # 노이즈 생성
        if self.animated or self.seed is None:
            self._rng = np.random.default_rng(self.seed if not self.animated else None)

        if self.monochrome:
            noise = self._rng.uniform(-1, 1, (height, width, 1))
            if len(img.shape) == 3:
                noise = np.repeat(noise, img.shape[2], axis=2)
        else:
            channels = img.shape[2] if len(img.shape) == 3 else 1
            noise = self._rng.uniform(-1, 1, (height, width, channels))

        # 노이즈 적용
        result = img + noise * self.intensity
        result = np.clip(result, 0, 1)

        return self._ensure_uint8(result) if is_uint8 else result

    def reset_seed(self, seed: int = None) -> None:
        """랜덤 시드 재설정"""
        self.seed = seed
        self._rng = np.random.default_rng(seed)


class GlitchEffect(BaseEffect):
    """
    글리치 효과

    간헐적인 강한 왜곡을 재현합니다.
    """

    def __init__(
        self,
        enabled: bool = True,
        intensity: float = 0.3,
        frequency: float = 0.1,
        block_size: int = 16,
        color_shift: bool = True,
    ):
        """
        글리치 효과 초기화

        Args:
            enabled: 효과 활성화 여부
            intensity: 글리치 강도 (0.0 ~ 1.0)
            frequency: 글리치 발생 빈도 (0.0 ~ 1.0)
            block_size: 글리치 블록 크기
            color_shift: 색상 채널 이동 여부
        """
        super().__init__(enabled, intensity)
        self.frequency = frequency
        self.block_size = block_size
        self.color_shift = color_shift
        self._rng = np.random.default_rng()

    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        글리치 효과 적용

        Args:
            image: 입력 이미지 (H, W, C)

        Returns:
            글리치가 적용된 이미지
        """
        if not self.enabled:
            return image

        # 글리치 발생 여부 결정
        if self._rng.random() > self.frequency:
            return image

        is_uint8 = image.dtype == np.uint8
        img = self._ensure_float(image).copy()
        height, width = img.shape[:2]

        # 글리치 블록 수 결정
        num_blocks = int(self.intensity * 10) + 1

        for _ in range(num_blocks):
            # 랜덤 블록 영역 선택
            block_height = self._rng.integers(self.block_size, self.block_size * 4)
            block_width = self._rng.integers(width // 4, width)
            y = self._rng.integers(0, max(1, height - block_height))
            x = self._rng.integers(0, max(1, width - block_width))

            # 블록 이동
            shift = self._rng.integers(-width // 4, width // 4)
            x_end = min(x + block_width, width)
            y_end = min(y + block_height, height)

            block = img[y:y_end, x:x_end].copy()

            # 수평 이동
            new_x = max(0, min(x + shift, width - block.shape[1]))
            img[y:y_end, new_x : new_x + block.shape[1]] = block

            # 색상 채널 이동
            if self.color_shift and len(img.shape) == 3:
                channel = self._rng.integers(0, 3)
                channel_shift = self._rng.integers(-5, 6)
                img[y:y_end, :, channel] = np.roll(
                    img[y:y_end, :, channel], channel_shift, axis=1
                )

        return self._ensure_uint8(img) if is_uint8 else img
