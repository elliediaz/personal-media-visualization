"""
Bloom 효과 (빛 번짐)

CRT 형광체의 발광 특성을 재현합니다.
"""

import numpy as np
from scipy import ndimage

from .base_effect import BaseEffect


class BloomEffect(BaseEffect):
    """
    Bloom 효과

    밝은 영역 주변에 광채 효과를 추가합니다.
    """

    def __init__(
        self,
        enabled: bool = True,
        intensity: float = 0.4,
        radius: int = 5,
        threshold: float = 0.6,
        soft_threshold: bool = True,
    ):
        """
        Bloom 효과 초기화

        Args:
            enabled: 효과 활성화 여부
            intensity: Bloom 강도 (0.0 ~ 1.0)
            radius: 블러 반경 (픽셀)
            threshold: 밝기 임계값 (0.0 ~ 1.0)
            soft_threshold: 부드러운 임계값 적용 여부
        """
        super().__init__(enabled, intensity)
        self.radius = max(1, radius)
        self.threshold = max(0.0, min(1.0, threshold))
        self.soft_threshold = soft_threshold

    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        Bloom 효과 적용

        Args:
            image: 입력 이미지 (H, W, C)

        Returns:
            Bloom이 적용된 이미지
        """
        if not self.enabled or self.intensity == 0:
            return image

        is_uint8 = image.dtype == np.uint8
        img = self._ensure_float(image)

        # 밝은 영역 추출
        if len(img.shape) == 3:
            luminance = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
        else:
            luminance = img

        # 임계값 적용
        if self.soft_threshold:
            # 부드러운 임계값: sigmoid 유사 함수
            softness = 0.1
            bright_mask = np.clip((luminance - self.threshold) / softness + 0.5, 0, 1)
        else:
            bright_mask = (luminance > self.threshold).astype(np.float32)

        # 밝은 영역만 추출
        if len(img.shape) == 3:
            bright_areas = img * bright_mask[:, :, np.newaxis]
        else:
            bright_areas = img * bright_mask

        # 가우시안 블러 적용
        sigma = self.radius / 2
        if len(img.shape) == 3:
            blurred = np.zeros_like(bright_areas)
            for c in range(img.shape[2]):
                blurred[:, :, c] = ndimage.gaussian_filter(
                    bright_areas[:, :, c], sigma=sigma
                )
        else:
            blurred = ndimage.gaussian_filter(bright_areas, sigma=sigma)

        # 원본과 Bloom 합성
        result = img + blurred * self.intensity
        result = np.clip(result, 0, 1)

        return self._ensure_uint8(result) if is_uint8 else result


class HDRBloomEffect(BaseEffect):
    """
    HDR Bloom 효과

    여러 레벨의 블러를 합성하여 더 자연스러운 Bloom을 생성합니다.
    """

    def __init__(
        self,
        enabled: bool = True,
        intensity: float = 0.5,
        levels: int = 4,
        base_radius: int = 4,
        threshold: float = 0.5,
    ):
        """
        HDR Bloom 효과 초기화

        Args:
            enabled: 효과 활성화 여부
            intensity: Bloom 강도 (0.0 ~ 1.0)
            levels: Bloom 레벨 수
            base_radius: 기본 블러 반경
            threshold: 밝기 임계값
        """
        super().__init__(enabled, intensity)
        self.levels = max(1, levels)
        self.base_radius = max(1, base_radius)
        self.threshold = max(0.0, min(1.0, threshold))

    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        HDR Bloom 효과 적용

        Args:
            image: 입력 이미지 (H, W, C)

        Returns:
            Bloom이 적용된 이미지
        """
        if not self.enabled or self.intensity == 0:
            return image

        is_uint8 = image.dtype == np.uint8
        img = self._ensure_float(image)

        # 밝은 영역 추출
        if len(img.shape) == 3:
            luminance = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
        else:
            luminance = img

        bright_mask = np.clip((luminance - self.threshold) * 2, 0, 1)

        if len(img.shape) == 3:
            bright_areas = img * bright_mask[:, :, np.newaxis]
        else:
            bright_areas = img * bright_mask

        # 여러 레벨의 블러 합성
        bloom = np.zeros_like(img)
        for level in range(self.levels):
            radius = self.base_radius * (2**level)
            sigma = radius / 2
            weight = 1.0 / (level + 1)

            if len(img.shape) == 3:
                for c in range(img.shape[2]):
                    bloom[:, :, c] += (
                        ndimage.gaussian_filter(bright_areas[:, :, c], sigma=sigma)
                        * weight
                    )
            else:
                bloom += ndimage.gaussian_filter(bright_areas, sigma=sigma) * weight

        # 정규화 및 합성
        bloom /= sum(1.0 / (i + 1) for i in range(self.levels))
        result = img + bloom * self.intensity
        result = np.clip(result, 0, 1)

        return self._ensure_uint8(result) if is_uint8 else result
