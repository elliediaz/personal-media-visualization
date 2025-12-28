"""
레트로 색상 팔레트 정의

C64, EGA, VGA 등 클래식 색상 팔레트를 제공합니다.
"""

from typing import Tuple

import numpy as np


# 타입 정의
RGB = Tuple[int, int, int]
Palette = list[RGB]


class RetroPalettes:
    """
    레트로 색상 팔레트 컬렉션
    """

    # C64 팔레트 (16색)
    C64: Palette = [
        (0x00, 0x00, 0x00),  # Black
        (0xFF, 0xFF, 0xFF),  # White
        (0x88, 0x00, 0x00),  # Red
        (0xAA, 0xFF, 0xEE),  # Cyan
        (0xCC, 0x44, 0xCC),  # Purple
        (0x00, 0xCC, 0x55),  # Green
        (0x00, 0x00, 0xAA),  # Blue
        (0xEE, 0xEE, 0x77),  # Yellow
        (0xDD, 0x88, 0x55),  # Orange
        (0x66, 0x44, 0x00),  # Brown
        (0xFF, 0x77, 0x77),  # Light Red
        (0x33, 0x33, 0x33),  # Dark Gray
        (0x77, 0x77, 0x77),  # Gray
        (0xAA, 0xFF, 0x66),  # Light Green
        (0x00, 0x88, 0xFF),  # Light Blue
        (0xBB, 0xBB, 0xBB),  # Light Gray
    ]

    # EGA 팔레트 (16색)
    EGA: Palette = [
        (0x00, 0x00, 0x00),  # Black
        (0x00, 0x00, 0xAA),  # Blue
        (0x00, 0xAA, 0x00),  # Green
        (0x00, 0xAA, 0xAA),  # Cyan
        (0xAA, 0x00, 0x00),  # Red
        (0xAA, 0x00, 0xAA),  # Magenta
        (0xAA, 0x55, 0x00),  # Brown
        (0xAA, 0xAA, 0xAA),  # Light Gray
        (0x55, 0x55, 0x55),  # Dark Gray
        (0x55, 0x55, 0xFF),  # Bright Blue
        (0x55, 0xFF, 0x55),  # Bright Green
        (0x55, 0xFF, 0xFF),  # Bright Cyan
        (0xFF, 0x55, 0x55),  # Bright Red
        (0xFF, 0x55, 0xFF),  # Bright Magenta
        (0xFF, 0xFF, 0x55),  # Yellow
        (0xFF, 0xFF, 0xFF),  # White
    ]

    # VGA 기본 팔레트 (16색)
    VGA: Palette = [
        (0x00, 0x00, 0x00),  # Black
        (0x00, 0x00, 0xAA),  # Blue
        (0x00, 0xAA, 0x00),  # Green
        (0x00, 0xAA, 0xAA),  # Cyan
        (0xAA, 0x00, 0x00),  # Red
        (0xAA, 0x00, 0xAA),  # Magenta
        (0xAA, 0x55, 0x00),  # Brown
        (0xAA, 0xAA, 0xAA),  # Light Gray
        (0x55, 0x55, 0x55),  # Dark Gray
        (0x55, 0x55, 0xFF),  # Light Blue
        (0x55, 0xFF, 0x55),  # Light Green
        (0x55, 0xFF, 0xFF),  # Light Cyan
        (0xFF, 0x55, 0x55),  # Light Red
        (0xFF, 0x55, 0xFF),  # Light Magenta
        (0xFF, 0xFF, 0x55),  # Yellow
        (0xFF, 0xFF, 0xFF),  # White
    ]

    # 네온/사이버펑크 팔레트
    NEON: Palette = [
        (0x00, 0x00, 0x00),  # Black
        (0xFF, 0x00, 0xFF),  # Neon Pink
        (0x00, 0xFF, 0xFF),  # Neon Cyan
        (0xFF, 0xFF, 0x00),  # Neon Yellow
        (0x00, 0xFF, 0x00),  # Neon Green
        (0xFF, 0x66, 0x00),  # Neon Orange
        (0x99, 0x00, 0xFF),  # Neon Purple
        (0x00, 0x66, 0xFF),  # Neon Blue
        (0xFF, 0x00, 0x33),  # Neon Red
        (0xFF, 0x69, 0xB4),  # Hot Pink
        (0x7B, 0x68, 0xEE),  # Medium Slate Blue
        (0x00, 0xFA, 0x9A),  # Medium Spring Green
        (0xFF, 0x14, 0x93),  # Deep Pink
        (0x00, 0xCE, 0xD1),  # Dark Turquoise
        (0xFF, 0xD7, 0x00),  # Gold
        (0xE0, 0xE0, 0xE0),  # Light Gray
    ]

    # Synthwave 팔레트
    SYNTHWAVE: Palette = [
        (0x1A, 0x0A, 0x2E),  # Dark Purple
        (0x3D, 0x1A, 0x78),  # Purple
        (0xB9, 0x1A, 0xFF),  # Magenta
        (0xFF, 0x00, 0xFF),  # Pink
        (0xFF, 0x14, 0x93),  # Hot Pink
        (0xFF, 0x6B, 0x35),  # Orange
        (0xFF, 0xD7, 0x00),  # Yellow
        (0x00, 0xD4, 0xFF),  # Cyan
        (0x00, 0x77, 0xFF),  # Blue
        (0x2E, 0x0A, 0x1A),  # Dark Red
        (0x78, 0x1A, 0x3D),  # Wine
        (0xFF, 0x1A, 0xB9),  # Bright Pink
        (0x35, 0x6B, 0xFF),  # Bright Blue
        (0x00, 0xFF, 0xD4),  # Bright Cyan
        (0xD7, 0xFF, 0x00),  # Lime
        (0xE0, 0xE0, 0xE0),  # Light Gray
    ]

    # CRT 그린 모노크롬
    CRT_GREEN: Palette = [
        (0x00, 0x11, 0x00),  # Darkest
        (0x00, 0x22, 0x00),
        (0x00, 0x33, 0x00),
        (0x00, 0x44, 0x00),
        (0x00, 0x55, 0x00),
        (0x00, 0x66, 0x00),
        (0x00, 0x77, 0x00),
        (0x00, 0x88, 0x00),
        (0x00, 0x99, 0x00),
        (0x00, 0xAA, 0x00),
        (0x00, 0xBB, 0x00),
        (0x00, 0xCC, 0x00),
        (0x00, 0xDD, 0x00),
        (0x00, 0xEE, 0x00),
        (0x00, 0xFF, 0x00),  # Brightest
        (0x66, 0xFF, 0x66),  # Highlight
    ]

    # CRT 앰버 모노크롬
    CRT_AMBER: Palette = [
        (0x1A, 0x0A, 0x00),  # Darkest
        (0x2D, 0x14, 0x00),
        (0x3D, 0x1F, 0x00),
        (0x4D, 0x29, 0x00),
        (0x5C, 0x33, 0x00),
        (0x6B, 0x3D, 0x00),
        (0x7A, 0x47, 0x00),
        (0x8A, 0x52, 0x00),
        (0x99, 0x5C, 0x00),
        (0xA8, 0x66, 0x00),
        (0xB8, 0x70, 0x00),
        (0xC7, 0x7A, 0x00),
        (0xD6, 0x85, 0x00),
        (0xE6, 0x8F, 0x00),
        (0xFF, 0xAA, 0x00),  # Brightest
        (0xFF, 0xCC, 0x66),  # Highlight
    ]

    # Windows 95 시스템 색상
    WIN95: Palette = [
        (0x00, 0x80, 0x80),  # Desktop (Teal)
        (0xC0, 0xC0, 0xC0),  # Window (Silver)
        (0x00, 0x00, 0x80),  # Title Active (Navy)
        (0x80, 0x80, 0x80),  # Title Inactive (Gray)
        (0xFF, 0xFF, 0xFF),  # Title Text Active
        (0x00, 0x00, 0x00),  # Text
        (0xDF, 0xDF, 0xDF),  # Button Light
        (0x00, 0x00, 0x00),  # Button Dark Shadow
        (0xFF, 0xFF, 0x00),  # Highlight
        (0xFF, 0x00, 0x00),  # Error
        (0x00, 0xFF, 0x00),  # Success
        (0x00, 0x00, 0xFF),  # Link
        (0x80, 0x00, 0x80),  # Visited Link
        (0xFF, 0x80, 0x00),  # Warning
        (0x80, 0x80, 0x00),  # Olive
        (0x00, 0x80, 0x00),  # Dark Green
    ]

    @classmethod
    def get_palette(cls, name: str) -> Palette:
        """
        이름으로 팔레트 가져오기

        Args:
            name: 팔레트 이름 (c64, ega, vga, neon, synthwave, crt_green, crt_amber, win95)

        Returns:
            색상 팔레트

        Raises:
            ValueError: 알 수 없는 팔레트 이름
        """
        palettes = {
            "c64": cls.C64,
            "ega": cls.EGA,
            "vga": cls.VGA,
            "neon": cls.NEON,
            "synthwave": cls.SYNTHWAVE,
            "crt_green": cls.CRT_GREEN,
            "crt_amber": cls.CRT_AMBER,
            "win95": cls.WIN95,
        }

        name_lower = name.lower()
        if name_lower not in palettes:
            raise ValueError(f"알 수 없는 팔레트: {name}. 사용 가능: {list(palettes.keys())}")

        return palettes[name_lower]

    @classmethod
    def list_palettes(cls) -> list[str]:
        """사용 가능한 팔레트 목록 반환"""
        return ["c64", "ega", "vga", "neon", "synthwave", "crt_green", "crt_amber", "win95"]


def rgb_to_hex(rgb: RGB) -> str:
    """RGB 튜플을 HEX 문자열로 변환"""
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def hex_to_rgb(hex_color: str) -> RGB:
    """HEX 문자열을 RGB 튜플로 변환"""
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def quantize_to_palette(image: np.ndarray, palette: Palette) -> np.ndarray:
    """
    이미지를 팔레트 색상으로 양자화

    Args:
        image: 입력 이미지 (H, W, 3), uint8
        palette: 색상 팔레트

    Returns:
        양자화된 이미지
    """
    palette_array = np.array(palette, dtype=np.uint8)
    h, w = image.shape[:2]

    # 이미지를 1D로 펼침
    pixels = image.reshape(-1, 3).astype(np.float32)

    # 각 픽셀에서 팔레트 색상까지의 거리 계산
    distances = np.zeros((pixels.shape[0], len(palette)))
    for i, color in enumerate(palette_array):
        distances[:, i] = np.sum((pixels - color.astype(np.float32)) ** 2, axis=1)

    # 가장 가까운 팔레트 색상 선택
    indices = np.argmin(distances, axis=1)
    result = palette_array[indices]

    return result.reshape(h, w, 3)


def create_gradient_palette(color1: RGB, color2: RGB, steps: int = 16) -> Palette:
    """
    두 색상 사이의 그라디언트 팔레트 생성

    Args:
        color1: 시작 색상
        color2: 끝 색상
        steps: 단계 수

    Returns:
        그라디언트 팔레트
    """
    palette = []
    for i in range(steps):
        t = i / (steps - 1)
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)
        palette.append((r, g, b))
    return palette


def palette_to_matplotlib_cmap(palette: Palette, name: str = "retro"):
    """
    팔레트를 matplotlib colormap으로 변환

    Args:
        palette: 색상 팔레트
        name: colormap 이름

    Returns:
        matplotlib LinearSegmentedColormap
    """
    from matplotlib.colors import LinearSegmentedColormap

    colors = [(r / 255, g / 255, b / 255) for r, g, b in palette]
    return LinearSegmentedColormap.from_list(name, colors)
