"""
CRT 효과 기본 추상 클래스
"""

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np


class BaseEffect(ABC):
    """
    CRT 효과 기본 클래스

    모든 CRT 효과가 상속해야 하는 추상 클래스입니다.
    """

    def __init__(self, enabled: bool = True, intensity: float = 1.0):
        """
        효과 초기화

        Args:
            enabled: 효과 활성화 여부
            intensity: 효과 강도 (0.0 ~ 1.0)
        """
        self.enabled = enabled
        self.intensity = max(0.0, min(1.0, intensity))

    @abstractmethod
    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        이미지에 효과 적용

        Args:
            image: 입력 이미지 (RGB, uint8 또는 float)

        Returns:
            효과가 적용된 이미지
        """
        pass

    def _ensure_float(self, image: np.ndarray) -> np.ndarray:
        """이미지를 float 형식으로 변환"""
        if image.dtype == np.uint8:
            return image.astype(np.float32) / 255.0
        return image.astype(np.float32)

    def _ensure_uint8(self, image: np.ndarray) -> np.ndarray:
        """이미지를 uint8 형식으로 변환"""
        if image.dtype != np.uint8:
            return (np.clip(image, 0, 1) * 255).astype(np.uint8)
        return image

    def _blend(
        self, original: np.ndarray, effect: np.ndarray, alpha: Optional[float] = None
    ) -> np.ndarray:
        """
        원본과 효과 이미지 블렌딩

        Args:
            original: 원본 이미지
            effect: 효과 이미지
            alpha: 블렌딩 비율 (None이면 self.intensity 사용)

        Returns:
            블렌딩된 이미지
        """
        alpha = alpha if alpha is not None else self.intensity
        return original * (1 - alpha) + effect * alpha

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(enabled={self.enabled}, intensity={self.intensity})"
