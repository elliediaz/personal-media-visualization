"""
스캔라인 효과

CRT 모니터의 수평 주사선을 시뮬레이션합니다.
"""

import numpy as np

from .base_effect import BaseEffect


class ScanlinesEffect(BaseEffect):
    """
    스캔라인 효과

    CRT 모니터의 수평 주사선을 재현합니다.
    """

    def __init__(
        self,
        enabled: bool = True,
        intensity: float = 0.3,
        line_width: int = 2,
        gap: int = 2,
        animated: bool = False,
        phase: float = 0.0,
    ):
        """
        스캔라인 효과 초기화

        Args:
            enabled: 효과 활성화 여부
            intensity: 스캔라인 어두움 정도 (0.0 ~ 1.0)
            line_width: 스캔라인 너비 (픽셀)
            gap: 스캔라인 간격 (픽셀)
            animated: 애니메이션 여부
            phase: 애니메이션 위상 (0.0 ~ 1.0)
        """
        super().__init__(enabled, intensity)
        self.line_width = max(1, line_width)
        self.gap = max(1, gap)
        self.animated = animated
        self.phase = phase

    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        스캔라인 효과 적용

        Args:
            image: 입력 이미지 (H, W, C)

        Returns:
            스캔라인이 적용된 이미지
        """
        if not self.enabled:
            return image

        is_uint8 = image.dtype == np.uint8
        img = self._ensure_float(image)
        height, width = img.shape[:2]

        # 스캔라인 마스크 생성
        mask = np.ones((height, 1), dtype=np.float32)
        period = self.line_width + self.gap

        # 애니메이션 오프셋 계산
        offset = int(self.phase * period) if self.animated else 0

        for y in range(height):
            y_shifted = (y + offset) % period
            if y_shifted < self.line_width:
                # 스캔라인 영역 (어둡게)
                mask[y] = 1.0 - self.intensity
            else:
                # 갭 영역 (원본 유지)
                mask[y] = 1.0

        # 마스크 적용 (모든 채널에)
        if len(img.shape) == 3:
            mask = mask.reshape(height, 1, 1)
            result = img * mask
        else:
            result = img * mask.flatten()

        return self._ensure_uint8(result) if is_uint8 else result

    def update_phase(self, delta: float = 0.02) -> None:
        """
        애니메이션 위상 업데이트

        Args:
            delta: 위상 변화량
        """
        self.phase = (self.phase + delta) % 1.0
