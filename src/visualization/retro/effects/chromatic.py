"""
RGB 색수차 (Chromatic Aberration) 효과

CRT의 RGB 전자총 정렬 오차를 시뮬레이션합니다.
"""

import numpy as np
from scipy import ndimage

from .base_effect import BaseEffect


class ChromaticAberrationEffect(BaseEffect):
    """
    RGB 색수차 효과

    R, G, B 채널을 미세하게 오프셋하여 색수차를 재현합니다.
    """

    def __init__(
        self,
        enabled: bool = True,
        intensity: float = 1.0,
        offset: int = 2,
        radial: bool = True,
    ):
        """
        색수차 효과 초기화

        Args:
            enabled: 효과 활성화 여부
            intensity: 효과 강도 (0.0 ~ 1.0)
            offset: 채널 오프셋 (픽셀)
            radial: 방사형 왜곡 여부 (True: 가장자리로 갈수록 강함)
        """
        super().__init__(enabled, intensity)
        self.offset = offset
        self.radial = radial

    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        색수차 효과 적용

        Args:
            image: 입력 이미지 (H, W, C)

        Returns:
            색수차가 적용된 이미지
        """
        if not self.enabled or len(image.shape) < 3:
            return image

        is_uint8 = image.dtype == np.uint8
        img = self._ensure_float(image)
        height, width = img.shape[:2]

        # 각 채널 분리
        r_channel = img[:, :, 0]
        g_channel = img[:, :, 1]
        b_channel = img[:, :, 2]

        # 오프셋 계산 (intensity 반영)
        actual_offset = self.offset * self.intensity

        if self.radial:
            # 방사형 왜곡: 중심에서 멀어질수록 효과 강화
            result = self._apply_radial_aberration(img, actual_offset)
        else:
            # 단순 오프셋
            r_shifted = ndimage.shift(r_channel, [0, actual_offset], mode="nearest")
            b_shifted = ndimage.shift(b_channel, [0, -actual_offset], mode="nearest")
            result = np.stack([r_shifted, g_channel, b_shifted], axis=2)

        return self._ensure_uint8(result) if is_uint8 else result

    def _apply_radial_aberration(
        self, image: np.ndarray, max_offset: float
    ) -> np.ndarray:
        """
        방사형 색수차 적용

        Args:
            image: 입력 이미지
            max_offset: 최대 오프셋

        Returns:
            방사형 색수차가 적용된 이미지
        """
        height, width = image.shape[:2]
        center_y, center_x = height / 2, width / 2

        # 좌표 그리드 생성
        y, x = np.ogrid[:height, :width]

        # 중심으로부터의 정규화된 거리
        dist_y = (y - center_y) / center_y
        dist_x = (x - center_x) / center_x
        dist = np.sqrt(dist_x**2 + dist_y**2)
        dist = np.clip(dist, 0, 1)

        # R 채널: 바깥으로 확대
        r_scale = 1.0 + (max_offset / 100) * dist
        r_channel = self._radial_scale(image[:, :, 0], r_scale)

        # G 채널: 원본 유지
        g_channel = image[:, :, 1]

        # B 채널: 안쪽으로 축소
        b_scale = 1.0 - (max_offset / 100) * dist
        b_channel = self._radial_scale(image[:, :, 2], b_scale)

        return np.stack([r_channel, g_channel, b_channel], axis=2)

    def _radial_scale(self, channel: np.ndarray, scale: np.ndarray) -> np.ndarray:
        """
        채널을 방사형으로 스케일

        Args:
            channel: 단일 채널
            scale: 스케일 맵

        Returns:
            스케일된 채널
        """
        height, width = channel.shape
        center_y, center_x = height / 2, width / 2

        # 좌표 그리드
        y, x = np.meshgrid(np.arange(height), np.arange(width), indexing="ij")

        # 새 좌표 계산
        new_y = center_y + (y - center_y) / np.maximum(scale, 0.01)
        new_x = center_x + (x - center_x) / np.maximum(scale, 0.01)

        # 경계 처리
        new_y = np.clip(new_y, 0, height - 1)
        new_x = np.clip(new_x, 0, width - 1)

        # 쌍선형 보간
        y0 = np.floor(new_y).astype(int)
        y1 = np.minimum(y0 + 1, height - 1)
        x0 = np.floor(new_x).astype(int)
        x1 = np.minimum(x0 + 1, width - 1)

        fy = new_y - y0
        fx = new_x - x0

        result = (
            channel[y0, x0] * (1 - fy) * (1 - fx)
            + channel[y1, x0] * fy * (1 - fx)
            + channel[y0, x1] * (1 - fy) * fx
            + channel[y1, x1] * fy * fx
        )

        return result
