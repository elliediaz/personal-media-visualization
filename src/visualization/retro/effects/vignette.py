"""
비네트 및 화면 곡률 효과

CRT 브라운관의 볼록한 화면 특성을 재현합니다.
"""

import numpy as np

from .base_effect import BaseEffect


class VignetteEffect(BaseEffect):
    """
    비네트 효과

    화면 가장자리를 어둡게 처리합니다.
    """

    def __init__(
        self,
        enabled: bool = True,
        intensity: float = 0.6,
        radius: float = 0.8,
        softness: float = 0.5,
        shape: str = "ellipse",
    ):
        """
        비네트 효과 초기화

        Args:
            enabled: 효과 활성화 여부
            intensity: 어두움 강도 (0.0 ~ 1.0)
            radius: 비네트 시작 반경 (0.0 ~ 1.0)
            softness: 가장자리 부드러움 (0.0 ~ 1.0)
            shape: 비네트 형태 ("ellipse", "circle", "rectangle")
        """
        super().__init__(enabled, intensity)
        self.radius = max(0.1, min(1.0, radius))
        self.softness = max(0.1, min(1.0, softness))
        self.shape = shape

    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        비네트 효과 적용

        Args:
            image: 입력 이미지 (H, W, C)

        Returns:
            비네트가 적용된 이미지
        """
        if not self.enabled or self.intensity == 0:
            return image

        is_uint8 = image.dtype == np.uint8
        img = self._ensure_float(image)
        height, width = img.shape[:2]

        # 비네트 마스크 생성
        mask = self._create_mask(height, width)

        # 마스크 적용
        if len(img.shape) == 3:
            mask = mask[:, :, np.newaxis]

        result = img * mask
        return self._ensure_uint8(result) if is_uint8 else result

    def _create_mask(self, height: int, width: int) -> np.ndarray:
        """
        비네트 마스크 생성

        Args:
            height: 이미지 높이
            width: 이미지 너비

        Returns:
            비네트 마스크 (0.0 ~ 1.0)
        """
        y, x = np.ogrid[:height, :width]
        center_y, center_x = height / 2, width / 2

        # 정규화된 좌표
        y_norm = (y - center_y) / center_y
        x_norm = (x - center_x) / center_x

        if self.shape == "circle":
            # 원형 비네트 (정사각형 비율)
            max_dim = max(height, width)
            y_norm = (y - center_y) / (max_dim / 2)
            x_norm = (x - center_x) / (max_dim / 2)
            dist = np.sqrt(x_norm**2 + y_norm**2)
        elif self.shape == "rectangle":
            # 사각형 비네트
            dist = np.maximum(np.abs(x_norm), np.abs(y_norm))
        else:
            # 타원형 비네트 (기본)
            dist = np.sqrt(x_norm**2 + y_norm**2)

        # 비네트 마스크 계산
        # radius: 비네트가 시작되는 거리
        # softness: 경계의 부드러움
        vignette = 1.0 - np.clip(
            (dist - self.radius) / (self.softness + 0.01), 0, 1
        )

        # 강도 적용
        mask = 1.0 - (1.0 - vignette) * self.intensity

        return mask.astype(np.float32)


class CurvatureEffect(BaseEffect):
    """
    화면 곡률 효과

    CRT 브라운관의 볼록한 화면을 시뮬레이션합니다.
    """

    def __init__(
        self,
        enabled: bool = True,
        intensity: float = 1.0,
        curvature: float = 0.03,
    ):
        """
        곡률 효과 초기화

        Args:
            enabled: 효과 활성화 여부
            intensity: 효과 강도 (0.0 ~ 1.0)
            curvature: 곡률 정도 (0.0 ~ 0.1)
        """
        super().__init__(enabled, intensity)
        self.curvature = max(0.0, min(0.1, curvature))

    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        곡률 효과 적용 (배럴 왜곡)

        Args:
            image: 입력 이미지 (H, W, C)

        Returns:
            곡률이 적용된 이미지
        """
        if not self.enabled or self.curvature == 0:
            return image

        is_uint8 = image.dtype == np.uint8
        img = self._ensure_float(image)
        height, width = img.shape[:2]

        # 좌표 그리드 생성
        y, x = np.meshgrid(np.arange(height), np.arange(width), indexing="ij")

        # 정규화된 좌표 (-1 ~ 1)
        x_norm = (x - width / 2) / (width / 2)
        y_norm = (y - height / 2) / (height / 2)

        # 중심으로부터의 거리
        r = np.sqrt(x_norm**2 + y_norm**2)

        # 배럴 왜곡 계수
        k = self.curvature * self.intensity

        # 왜곡된 좌표 계산
        r_distorted = r * (1 + k * r**2)

        # 정규화된 왜곡 좌표
        scale = np.where(r > 0, r_distorted / (r + 1e-10), 1)
        x_distorted = x_norm * scale
        y_distorted = y_norm * scale

        # 픽셀 좌표로 변환
        x_new = (x_distorted * (width / 2) + width / 2).astype(np.float32)
        y_new = (y_distorted * (height / 2) + height / 2).astype(np.float32)

        # 경계 체크
        valid = (
            (x_new >= 0) & (x_new < width - 1) & (y_new >= 0) & (y_new < height - 1)
        )

        # 쌍선형 보간
        result = np.zeros_like(img)
        x0 = np.floor(x_new).astype(int)
        y0 = np.floor(y_new).astype(int)
        x1 = x0 + 1
        y1 = y0 + 1

        # 안전한 인덱싱
        x0_safe = np.clip(x0, 0, width - 1)
        x1_safe = np.clip(x1, 0, width - 1)
        y0_safe = np.clip(y0, 0, height - 1)
        y1_safe = np.clip(y1, 0, height - 1)

        # 보간 가중치
        fx = x_new - x0
        fy = y_new - y0

        if len(img.shape) == 3:
            for c in range(img.shape[2]):
                result[:, :, c] = (
                    img[y0_safe, x0_safe, c] * (1 - fx) * (1 - fy)
                    + img[y1_safe, x0_safe, c] * fy * (1 - fx)
                    + img[y0_safe, x1_safe, c] * (1 - fy) * fx
                    + img[y1_safe, x1_safe, c] * fy * fx
                ) * valid
        else:
            result = (
                img[y0_safe, x0_safe] * (1 - fx) * (1 - fy)
                + img[y1_safe, x0_safe] * fy * (1 - fx)
                + img[y0_safe, x1_safe] * (1 - fy) * fx
                + img[y1_safe, x1_safe] * fy * fx
            ) * valid

        return self._ensure_uint8(result) if is_uint8 else result
