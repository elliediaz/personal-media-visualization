"""
시각화 스타일 모듈

50개 이상의 다양한 오디오 시각화 스타일을 제공합니다.
"""

import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, List, Optional, Callable

import numpy as np

try:
    import pygame
    from pygame import Surface, Rect
except ImportError:
    pass


class VisualizationCategory(Enum):
    """시각화 카테고리"""
    WAVEFORM = "파형"
    SPECTRUM = "스펙트럼"
    METER = "미터"
    SCOPE = "스코프"
    PATTERN = "패턴"
    ARTISTIC = "아티스틱"
    RETRO = "레트로"
    SCIENTIFIC = "과학적"
    SPATIAL = "공간"
    EXPERIMENTAL = "실험적"


@dataclass
class VisualizationInfo:
    """시각화 정보"""
    id: str
    name: str
    name_kr: str
    category: VisualizationCategory
    description: str


class BaseVisualization(ABC):
    """시각화 베이스 클래스"""

    def __init__(self, rect: Rect, colors: dict):
        self.rect = rect
        self.colors = colors
        self.time = 0

    @abstractmethod
    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        """시각화 렌더링"""
        pass

    def update(self, dt: float):
        """상태 업데이트"""
        self.time += dt


# ==================== 파형 시각화 ====================

class WaveformLine(BaseVisualization):
    """01. 기본 파형 (선)"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 2:
            return

        cy = self.rect.centery
        points = []

        for i, val in enumerate(waveform):
            x = self.rect.x + int(i * self.rect.width / len(waveform))
            y = cy - int(val * self.rect.height * 0.4)
            points.append((x, y))

        if len(points) > 1:
            pygame.draw.lines(surface, self.colors['bright'], False, points, 2)


class WaveformFilled(BaseVisualization):
    """02. 채워진 파형"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 2:
            return

        cy = self.rect.centery
        points_top = []
        points_bottom = []

        for i, val in enumerate(waveform):
            x = self.rect.x + int(i * self.rect.width / len(waveform))
            y_top = cy - int(val * self.rect.height * 0.4)
            points_top.append((x, y_top))
            points_bottom.append((x, cy))

        if len(points_top) > 1:
            polygon = points_top + points_bottom[::-1]
            pygame.draw.polygon(surface, self.colors['dim'], polygon)
            pygame.draw.lines(surface, self.colors['bright'], False, points_top, 2)


class WaveformMirror(BaseVisualization):
    """03. 미러 파형"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 2:
            return

        cy = self.rect.centery
        half_h = self.rect.height * 0.4

        for i, val in enumerate(waveform):
            x = self.rect.x + int(i * self.rect.width / len(waveform))
            h = int(abs(val) * half_h)
            pygame.draw.line(surface, self.colors['foreground'],
                           (x, cy - h), (x, cy + h), 1)


class WaveformBars(BaseVisualization):
    """04. 파형 바"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 2:
            return

        cy = self.rect.centery
        bar_count = 64
        samples_per_bar = len(waveform) // bar_count
        bar_width = max(1, self.rect.width // bar_count - 1)

        for i in range(bar_count):
            start = i * samples_per_bar
            end = min(start + samples_per_bar, len(waveform))
            val = np.mean(np.abs(waveform[start:end]))

            x = self.rect.x + i * (bar_width + 1)
            h = int(val * self.rect.height * 0.8)

            pygame.draw.rect(surface, self.colors['foreground'],
                           (x, cy - h // 2, bar_width, h))


class WaveformDots(BaseVisualization):
    """05. 점 파형"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 2:
            return

        cy = self.rect.centery
        step = max(1, len(waveform) // 200)

        for i in range(0, len(waveform), step):
            x = self.rect.x + int(i * self.rect.width / len(waveform))
            y = cy - int(waveform[i] * self.rect.height * 0.4)
            pygame.draw.circle(surface, self.colors['bright'], (x, y), 2)


class WaveformGradient(BaseVisualization):
    """06. 그라데이션 파형"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 2:
            return

        cy = self.rect.centery

        for i in range(len(waveform) - 1):
            x1 = self.rect.x + int(i * self.rect.width / len(waveform))
            x2 = self.rect.x + int((i + 1) * self.rect.width / len(waveform))
            y1 = cy - int(waveform[i] * self.rect.height * 0.4)
            y2 = cy - int(waveform[i + 1] * self.rect.height * 0.4)

            intensity = min(1.0, abs(waveform[i]) * 2)
            color = self._lerp_color(self.colors['dim'], self.colors['bright'], intensity)
            pygame.draw.line(surface, color, (x1, y1), (x2, y2), 2)

    def _lerp_color(self, c1, c2, t):
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


class WaveformCircular(BaseVisualization):
    """07. 원형 파형"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 2:
            return

        cx = self.rect.centerx
        cy = self.rect.centery
        base_radius = min(self.rect.width, self.rect.height) * 0.3
        points = []

        for i, val in enumerate(waveform[::4]):
            angle = (i / (len(waveform) // 4)) * 2 * math.pi
            radius = base_radius + val * base_radius * 0.5
            x = cx + int(radius * math.cos(angle))
            y = cy + int(radius * math.sin(angle))
            points.append((x, y))

        if len(points) > 2:
            pygame.draw.polygon(surface, self.colors['foreground'], points, 2)


class WaveformSpiral(BaseVisualization):
    """08. 나선형 파형"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 2:
            return

        cx = self.rect.centerx
        cy = self.rect.centery
        max_radius = min(self.rect.width, self.rect.height) * 0.4
        points = []

        for i, val in enumerate(waveform[::2]):
            progress = i / (len(waveform) // 2)
            angle = progress * 6 * math.pi + self.time
            radius = progress * max_radius * (1 + val * 0.3)
            x = cx + int(radius * math.cos(angle))
            y = cy + int(radius * math.sin(angle))
            points.append((x, y))

        if len(points) > 1:
            pygame.draw.lines(surface, self.colors['bright'], False, points, 1)


# ==================== 스펙트럼 시각화 ====================

class SpectrumBars(BaseVisualization):
    """09. 스펙트럼 바"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(spectrum) < 1:
            return

        bar_width = max(1, self.rect.width // len(spectrum) - 1)

        for i, val in enumerate(spectrum):
            x = self.rect.x + i * (bar_width + 1)
            h = int(val * self.rect.height * 0.9)
            y = self.rect.y + self.rect.height - h

            pygame.draw.rect(surface, self.colors['foreground'],
                           (x, y, bar_width, h))


class SpectrumMirror(BaseVisualization):
    """10. 미러 스펙트럼"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(spectrum) < 1:
            return

        cy = self.rect.centery
        bar_width = max(1, self.rect.width // len(spectrum) - 1)

        for i, val in enumerate(spectrum):
            x = self.rect.x + i * (bar_width + 1)
            h = int(val * self.rect.height * 0.45)

            pygame.draw.rect(surface, self.colors['foreground'],
                           (x, cy - h, bar_width, h))
            pygame.draw.rect(surface, self.colors['dim'],
                           (x, cy, bar_width, h))


class SpectrumLine(BaseVisualization):
    """11. 스펙트럼 라인"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(spectrum) < 2:
            return

        points = []
        for i, val in enumerate(spectrum):
            x = self.rect.x + int(i * self.rect.width / len(spectrum))
            y = self.rect.y + self.rect.height - int(val * self.rect.height * 0.9)
            points.append((x, y))

        if len(points) > 1:
            pygame.draw.lines(surface, self.colors['bright'], False, points, 2)


class SpectrumFilled(BaseVisualization):
    """12. 채워진 스펙트럼"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(spectrum) < 2:
            return

        points = [(self.rect.x, self.rect.y + self.rect.height)]

        for i, val in enumerate(spectrum):
            x = self.rect.x + int(i * self.rect.width / len(spectrum))
            y = self.rect.y + self.rect.height - int(val * self.rect.height * 0.9)
            points.append((x, y))

        points.append((self.rect.x + self.rect.width, self.rect.y + self.rect.height))

        pygame.draw.polygon(surface, self.colors['dim'], points)
        pygame.draw.lines(surface, self.colors['bright'], False, points[1:-1], 2)


class SpectrumCircular(BaseVisualization):
    """13. 원형 스펙트럼"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(spectrum) < 1:
            return

        cx = self.rect.centerx
        cy = self.rect.centery
        base_radius = min(self.rect.width, self.rect.height) * 0.25

        for i, val in enumerate(spectrum):
            angle = (i / len(spectrum)) * 2 * math.pi - math.pi / 2
            inner_radius = base_radius
            outer_radius = base_radius + val * base_radius

            x1 = cx + int(inner_radius * math.cos(angle))
            y1 = cy + int(inner_radius * math.sin(angle))
            x2 = cx + int(outer_radius * math.cos(angle))
            y2 = cy + int(outer_radius * math.sin(angle))

            pygame.draw.line(surface, self.colors['foreground'], (x1, y1), (x2, y2), 2)


class SpectrumRadial(BaseVisualization):
    """14. 방사형 스펙트럼"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(spectrum) < 1:
            return

        cx = self.rect.centerx
        cy = self.rect.centery
        max_radius = min(self.rect.width, self.rect.height) * 0.4

        # 양쪽으로 미러링
        for side in [-1, 1]:
            for i, val in enumerate(spectrum):
                angle = side * (i / len(spectrum)) * math.pi - math.pi / 2
                radius = val * max_radius

                x = cx + int(radius * math.cos(angle))
                y = cy + int(radius * math.sin(angle))

                pygame.draw.line(surface, self.colors['foreground'],
                               (cx, cy), (x, y), 1)


class SpectrumWaterfall(BaseVisualization):
    """15. 폭포수 스펙트럼"""

    def __init__(self, rect: Rect, colors: dict):
        super().__init__(rect, colors)
        self.history = []
        self.max_history = 50

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(spectrum) < 1:
            return

        # 히스토리 업데이트
        self.history.append(spectrum.copy())
        if len(self.history) > self.max_history:
            self.history.pop(0)

        row_height = max(1, self.rect.height // self.max_history)
        col_width = max(1, self.rect.width // len(spectrum))

        for row_idx, row in enumerate(self.history):
            y = self.rect.y + row_idx * row_height
            for col_idx, val in enumerate(row):
                x = self.rect.x + col_idx * col_width
                intensity = int(val * 255)
                color = (0, intensity, 0) if self.colors['foreground'][1] > 100 else (intensity, intensity // 2, 0)
                pygame.draw.rect(surface, color, (x, y, col_width, row_height))


class Spectrogram3D(BaseVisualization):
    """16. 3D 스펙트로그램"""

    def __init__(self, rect: Rect, colors: dict):
        super().__init__(rect, colors)
        self.history = []
        self.max_history = 30

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(spectrum) < 1:
            return

        self.history.append(spectrum.copy())
        if len(self.history) > self.max_history:
            self.history.pop(0)

        depth_scale = 0.7
        x_offset = 3
        y_offset = 2

        for row_idx, row in enumerate(reversed(self.history)):
            depth = row_idx / self.max_history
            alpha = 1.0 - depth * 0.7

            for col_idx, val in enumerate(row[::2]):
                base_x = self.rect.x + col_idx * 8 + row_idx * x_offset
                base_y = self.rect.y + self.rect.height - row_idx * y_offset
                h = int(val * self.rect.height * 0.3 * (1 - depth * 0.3))

                color = tuple(int(c * alpha) for c in self.colors['foreground'])
                pygame.draw.line(surface, color,
                               (base_x, base_y), (base_x, base_y - h), 2)


# ==================== 미터 시각화 ====================

class VUMeter(BaseVisualization):
    """17. VU 미터"""

    def __init__(self, rect: Rect, colors: dict):
        super().__init__(rect, colors)
        self.level = 0
        self.peak = 0
        self.peak_hold = 0

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 1:
            return

        # RMS 레벨 계산
        rms = np.sqrt(np.mean(waveform ** 2))
        self.level = self.level * 0.8 + rms * 0.2

        # 피크 홀드
        if rms > self.peak:
            self.peak = rms
            self.peak_hold = 30
        else:
            self.peak_hold -= 1
            if self.peak_hold <= 0:
                self.peak *= 0.95

        # 미터 그리기
        meter_width = int(self.level * self.rect.width)
        peak_x = self.rect.x + int(self.peak * self.rect.width)

        pygame.draw.rect(surface, self.colors['dim'], self.rect, 1)
        pygame.draw.rect(surface, self.colors['foreground'],
                        (self.rect.x, self.rect.y, meter_width, self.rect.height))
        pygame.draw.line(surface, self.colors['bright'],
                        (peak_x, self.rect.y), (peak_x, self.rect.y + self.rect.height), 2)


class LevelMeter(BaseVisualization):
    """18. 레벨 미터 (세그먼트)"""

    def __init__(self, rect: Rect, colors: dict):
        super().__init__(rect, colors)
        self.levels = [0] * 16

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 1:
            return

        rms = np.sqrt(np.mean(waveform ** 2))
        active_segments = int(rms * 16)

        seg_width = self.rect.width // 16 - 2
        seg_height = self.rect.height - 4

        for i in range(16):
            x = self.rect.x + i * (seg_width + 2)
            y = self.rect.y + 2

            if i < active_segments:
                if i < 10:
                    color = self.colors['foreground']
                elif i < 14:
                    color = self.colors['warning']
                else:
                    color = self.colors['error']
            else:
                color = self.colors['dim']

            pygame.draw.rect(surface, color, (x, y, seg_width, seg_height))


class StereoMeter(BaseVisualization):
    """19. 스테레오 미터"""

    def __init__(self, rect: Rect, colors: dict):
        super().__init__(rect, colors)
        self.left = 0
        self.right = 0

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 2:
            return

        # 좌우 채널 시뮬레이션
        half = len(waveform) // 2
        left_rms = np.sqrt(np.mean(waveform[:half] ** 2))
        right_rms = np.sqrt(np.mean(waveform[half:] ** 2))

        self.left = self.left * 0.8 + left_rms * 0.2
        self.right = self.right * 0.8 + right_rms * 0.2

        cy = self.rect.centery
        half_height = self.rect.height // 2 - 5

        # 왼쪽 미터
        left_h = int(self.left * half_height)
        pygame.draw.rect(surface, self.colors['foreground'],
                        (self.rect.x, cy - left_h, self.rect.width // 2 - 5, left_h))

        # 오른쪽 미터
        right_h = int(self.right * half_height)
        pygame.draw.rect(surface, self.colors['foreground'],
                        (self.rect.x + self.rect.width // 2 + 5, cy - right_h,
                         self.rect.width // 2 - 5, right_h))


class PeakMeter(BaseVisualization):
    """20. 피크 미터"""

    def __init__(self, rect: Rect, colors: dict):
        super().__init__(rect, colors)
        self.peaks = []

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 1:
            return

        # 피크 감지
        peak = np.max(np.abs(waveform))
        self.peaks.append(peak)
        if len(self.peaks) > 100:
            self.peaks.pop(0)

        # 피크 히스토리 그리기
        for i, p in enumerate(self.peaks):
            x = self.rect.x + int(i * self.rect.width / 100)
            h = int(p * self.rect.height)
            y = self.rect.y + self.rect.height - h

            pygame.draw.line(surface, self.colors['foreground'],
                           (x, y), (x, self.rect.y + self.rect.height), 1)


# ==================== 스코프 시각화 ====================

class Oscilloscope(BaseVisualization):
    """21. 오실로스코프"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 2:
            return

        cy = self.rect.centery

        # 그리드
        for i in range(0, self.rect.width, 20):
            pygame.draw.line(surface, self.colors['dim'],
                           (self.rect.x + i, self.rect.y),
                           (self.rect.x + i, self.rect.y + self.rect.height))
        for i in range(0, self.rect.height, 20):
            pygame.draw.line(surface, self.colors['dim'],
                           (self.rect.x, self.rect.y + i),
                           (self.rect.x + self.rect.width, self.rect.y + i))

        # 파형
        points = []
        for i, val in enumerate(waveform):
            x = self.rect.x + int(i * self.rect.width / len(waveform))
            y = cy - int(val * self.rect.height * 0.4)
            points.append((x, y))

        if len(points) > 1:
            # 글로우 효과
            pygame.draw.lines(surface, self.colors['dim'], False, points, 4)
            pygame.draw.lines(surface, self.colors['bright'], False, points, 2)


class XYScope(BaseVisualization):
    """22. XY 스코프 (리사주)"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 4:
            return

        cx = self.rect.centerx
        cy = self.rect.centery
        scale = min(self.rect.width, self.rect.height) * 0.4

        # 그리드
        pygame.draw.line(surface, self.colors['dim'],
                        (self.rect.x, cy), (self.rect.x + self.rect.width, cy))
        pygame.draw.line(surface, self.colors['dim'],
                        (cx, self.rect.y), (cx, self.rect.y + self.rect.height))

        # XY 패턴
        points = []
        for i in range(0, len(waveform) - 1, 2):
            x = cx + int(waveform[i] * scale)
            y = cy - int(waveform[i + 1] * scale)
            points.append((x, y))

        for point in points:
            pygame.draw.circle(surface, self.colors['bright'], point, 1)


class Vectorscope(BaseVisualization):
    """23. 벡터스코프"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 4:
            return

        cx = self.rect.centerx
        cy = self.rect.centery
        radius = min(self.rect.width, self.rect.height) * 0.4

        # 원형 그리드
        pygame.draw.circle(surface, self.colors['dim'], (cx, cy), int(radius), 1)
        pygame.draw.circle(surface, self.colors['dim'], (cx, cy), int(radius * 0.5), 1)

        # 데이터 포인트
        for i in range(0, len(waveform) - 1, 2):
            angle = waveform[i] * math.pi
            r = abs(waveform[i + 1]) * radius

            x = cx + int(r * math.cos(angle))
            y = cy + int(r * math.sin(angle))

            pygame.draw.circle(surface, self.colors['foreground'], (x, y), 1)


class PhaseScope(BaseVisualization):
    """24. 위상 스코프"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 2:
            return

        cx = self.rect.centerx
        cy = self.rect.centery

        # 45도 회전된 그리드
        pygame.draw.line(surface, self.colors['dim'],
                        (self.rect.x, self.rect.y + self.rect.height),
                        (self.rect.x + self.rect.width, self.rect.y))
        pygame.draw.line(surface, self.colors['dim'],
                        (self.rect.x, self.rect.y),
                        (self.rect.x + self.rect.width, self.rect.y + self.rect.height))

        half = len(waveform) // 2
        scale = min(self.rect.width, self.rect.height) * 0.35

        for i in range(half):
            l = waveform[i]
            r = waveform[i + half] if i + half < len(waveform) else waveform[i]

            # M/S 변환
            mid = (l + r) / 2
            side = (l - r) / 2

            x = cx + int(side * scale)
            y = cy - int(mid * scale)

            pygame.draw.circle(surface, self.colors['foreground'], (x, y), 1)


# ==================== 패턴 시각화 ====================

class MatrixRain(BaseVisualization):
    """25. 매트릭스 레인"""

    def __init__(self, rect: Rect, colors: dict):
        super().__init__(rect, colors)
        self.columns = []
        self.chars = "ｱｲｳｴｵｶｷｸｹｺ0123456789"
        self._init_columns()

    def _init_columns(self):
        col_count = self.rect.width // 12
        for i in range(col_count):
            self.columns.append({
                'x': self.rect.x + i * 12,
                'y': random.randint(-self.rect.height, 0),
                'speed': random.randint(3, 8),
                'length': random.randint(5, 15),
            })

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        energy = np.mean(np.abs(waveform)) if len(waveform) > 0 else 0.5

        font = kwargs.get('font')
        if not font:
            return

        for col in self.columns:
            col['y'] += col['speed'] * (1 + energy)

            if col['y'] > self.rect.y + self.rect.height:
                col['y'] = self.rect.y - col['length'] * 14
                col['speed'] = random.randint(3, 8)

            for i in range(col['length']):
                y = int(col['y'] + i * 14)
                if self.rect.y <= y < self.rect.y + self.rect.height:
                    char = random.choice(self.chars)
                    alpha = 1.0 - i / col['length']
                    color = tuple(int(c * alpha) for c in self.colors['bright'])

                    text = font.render(char, color)
                    surface.blit(text, (col['x'], y))


class ASCIIWave(BaseVisualization):
    """26. ASCII 파형"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 1:
            return

        font = kwargs.get('font')
        if not font:
            return

        chars = " .:-=+*#%@"
        rows = self.rect.height // 14
        cols = self.rect.width // 8
        samples_per_col = max(1, len(waveform) // cols)

        for col in range(cols):
            start = col * samples_per_col
            end = min(start + samples_per_col, len(waveform))
            val = np.mean(np.abs(waveform[start:end]))

            char_idx = min(int(val * len(chars)), len(chars) - 1)
            char = chars[char_idx]

            row = rows // 2
            x = self.rect.x + col * 8
            y = self.rect.y + row * 14

            text = font.render(char, self.colors['foreground'])
            surface.blit(text, (x, y))


class BlockWave(BaseVisualization):
    """27. 블록 파형"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 1:
            return

        block_size = 8
        cols = self.rect.width // block_size
        rows = self.rect.height // block_size
        samples_per_col = max(1, len(waveform) // cols)

        for col in range(cols):
            start = col * samples_per_col
            end = min(start + samples_per_col, len(waveform))
            val = np.mean(np.abs(waveform[start:end]))

            active_rows = int(val * rows)
            center_row = rows // 2

            for row in range(active_rows):
                x = self.rect.x + col * block_size
                y1 = self.rect.y + (center_row - row - 1) * block_size
                y2 = self.rect.y + (center_row + row) * block_size

                pygame.draw.rect(surface, self.colors['foreground'],
                               (x, y1, block_size - 1, block_size - 1))
                pygame.draw.rect(surface, self.colors['foreground'],
                               (x, y2, block_size - 1, block_size - 1))


class Particles(BaseVisualization):
    """28. 파티클"""

    def __init__(self, rect: Rect, colors: dict):
        super().__init__(rect, colors)
        self.particles = []

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        energy = np.mean(np.abs(waveform)) if len(waveform) > 0 else 0

        # 새 파티클 생성
        if energy > 0.1 and len(self.particles) < 200:
            for _ in range(int(energy * 10)):
                self.particles.append({
                    'x': self.rect.centerx + random.randint(-20, 20),
                    'y': self.rect.centery,
                    'vx': random.uniform(-3, 3) * energy * 5,
                    'vy': random.uniform(-5, -1) * energy * 5,
                    'life': 1.0,
                })

        # 파티클 업데이트 및 렌더링
        new_particles = []
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.1  # 중력
            p['life'] -= 0.02

            if p['life'] > 0 and self.rect.collidepoint(int(p['x']), int(p['y'])):
                alpha = p['life']
                color = tuple(int(c * alpha) for c in self.colors['bright'])
                pygame.draw.circle(surface, color, (int(p['x']), int(p['y'])), 2)
                new_particles.append(p)

        self.particles = new_particles


class Starfield(BaseVisualization):
    """29. 스타필드"""

    def __init__(self, rect: Rect, colors: dict):
        super().__init__(rect, colors)
        self.stars = []
        for _ in range(100):
            self.stars.append({
                'x': random.randint(0, rect.width),
                'y': random.randint(0, rect.height),
                'z': random.uniform(0.1, 1.0),
            })

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        energy = np.mean(np.abs(waveform)) if len(waveform) > 0 else 0.3
        cx = self.rect.centerx
        cy = self.rect.centery

        for star in self.stars:
            star['z'] -= 0.02 * (1 + energy * 3)
            if star['z'] <= 0:
                star['x'] = random.randint(0, self.rect.width)
                star['y'] = random.randint(0, self.rect.height)
                star['z'] = 1.0

            # 원근 투영
            px = cx + int((star['x'] - cx) / star['z'])
            py = cy + int((star['y'] - cy) / star['z'])

            if self.rect.collidepoint(px, py):
                size = int(3 * (1 - star['z']))
                brightness = 1 - star['z']
                color = tuple(int(c * brightness) for c in self.colors['bright'])
                pygame.draw.circle(surface, color, (px, py), max(1, size))


class Tunnel(BaseVisualization):
    """30. 터널"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        cx = self.rect.centerx
        cy = self.rect.centery
        max_radius = min(self.rect.width, self.rect.height) * 0.5

        energy = np.mean(np.abs(waveform)) if len(waveform) > 0 else 0.3

        for i in range(10):
            radius = int(max_radius * (0.1 + i * 0.1) * (1 + energy * 0.5))
            offset = int(self.time * 50 + i * 20) % int(max_radius * 0.1)
            radius += offset

            if radius < max_radius:
                alpha = 1.0 - i * 0.1
                color = tuple(int(c * alpha) for c in self.colors['foreground'])
                pygame.draw.circle(surface, color, (cx, cy), radius, 1)


# ==================== 아티스틱 시각화 ====================

class Kaleidoscope(BaseVisualization):
    """31. 만화경"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(spectrum) < 1:
            return

        cx = self.rect.centerx
        cy = self.rect.centery
        segments = 8
        max_radius = min(self.rect.width, self.rect.height) * 0.4

        for seg in range(segments):
            angle_offset = (seg / segments) * 2 * math.pi + self.time

            for i, val in enumerate(spectrum[:32]):
                angle = angle_offset + (i / 32) * (2 * math.pi / segments)
                radius = val * max_radius

                x = cx + int(radius * math.cos(angle))
                y = cy + int(radius * math.sin(angle))

                pygame.draw.circle(surface, self.colors['foreground'], (x, y), 2)


class Mandala(BaseVisualization):
    """32. 만다라"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        cx = self.rect.centerx
        cy = self.rect.centery
        layers = 5
        points_per_layer = 12

        energy = np.mean(np.abs(waveform)) if len(waveform) > 0 else 0.5
        base_radius = min(self.rect.width, self.rect.height) * 0.1

        for layer in range(layers):
            radius = base_radius * (layer + 1) * (1 + energy * 0.3)

            for i in range(points_per_layer):
                angle = (i / points_per_layer) * 2 * math.pi + self.time * (layer + 1) * 0.1

                x = cx + int(radius * math.cos(angle))
                y = cy + int(radius * math.sin(angle))

                size = 3 + layer
                pygame.draw.circle(surface, self.colors['foreground'], (x, y), size, 1)


class FlowerPattern(BaseVisualization):
    """33. 꽃 패턴"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        cx = self.rect.centerx
        cy = self.rect.centery
        petals = 6

        energy = np.mean(np.abs(waveform)) if len(waveform) > 0 else 0.5
        max_radius = min(self.rect.width, self.rect.height) * 0.4

        for petal in range(petals):
            base_angle = (petal / petals) * 2 * math.pi + self.time * 0.5
            points = []

            for i in range(50):
                t = i / 50
                angle = base_angle + t * math.pi * 0.3
                radius = max_radius * math.sin(t * math.pi) * (0.5 + energy * 0.5)

                x = cx + int(radius * math.cos(angle))
                y = cy + int(radius * math.sin(angle))
                points.append((x, y))

            if len(points) > 1:
                pygame.draw.lines(surface, self.colors['foreground'], False, points, 2)


class GeometricShapes(BaseVisualization):
    """34. 기하학 도형"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        cx = self.rect.centerx
        cy = self.rect.centery

        energy = np.mean(np.abs(waveform)) if len(waveform) > 0 else 0.5

        # 회전하는 다각형들
        for sides in range(3, 8):
            radius = 30 + sides * 20 * (0.5 + energy * 0.5)
            rotation = self.time * (sides - 2) * 0.3

            points = []
            for i in range(sides):
                angle = rotation + (i / sides) * 2 * math.pi
                x = cx + int(radius * math.cos(angle))
                y = cy + int(radius * math.sin(angle))
                points.append((x, y))

            pygame.draw.polygon(surface, self.colors['foreground'], points, 1)


class SacredGeometry(BaseVisualization):
    """35. 신성 기하학"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        cx = self.rect.centerx
        cy = self.rect.centery

        energy = np.mean(np.abs(waveform)) if len(waveform) > 0 else 0.5
        radius = min(self.rect.width, self.rect.height) * 0.3 * (0.7 + energy * 0.3)

        # 생명의 꽃 패턴
        positions = [(cx, cy)]
        for i in range(6):
            angle = i * math.pi / 3
            x = cx + int(radius * math.cos(angle))
            y = cy + int(radius * math.sin(angle))
            positions.append((x, y))

        for pos in positions:
            pygame.draw.circle(surface, self.colors['foreground'], pos, int(radius), 1)


class WaveRings(BaseVisualization):
    """36. 파동 링"""

    def __init__(self, rect: Rect, colors: dict):
        super().__init__(rect, colors)
        self.rings = []

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        cx = self.rect.centerx
        cy = self.rect.centery
        max_radius = min(self.rect.width, self.rect.height) * 0.5

        energy = np.mean(np.abs(waveform)) if len(waveform) > 0 else 0

        # 새 링 추가
        if energy > 0.2 and (not self.rings or self.rings[-1]['radius'] > 20):
            self.rings.append({'radius': 5, 'alpha': 1.0})

        # 링 업데이트 및 렌더링
        new_rings = []
        for ring in self.rings:
            ring['radius'] += 3
            ring['alpha'] -= 0.02

            if ring['alpha'] > 0 and ring['radius'] < max_radius:
                color = tuple(int(c * ring['alpha']) for c in self.colors['foreground'])
                pygame.draw.circle(surface, color, (cx, cy), int(ring['radius']), 2)
                new_rings.append(ring)

        self.rings = new_rings


# ==================== 레트로 시각화 ====================

class Scanlines(BaseVisualization):
    """37. 스캔라인"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 1:
            return

        cy = self.rect.centery
        line_height = 3
        num_rows = max(1, self.rect.height // (line_height * 2))

        for y in range(self.rect.y, self.rect.y + self.rect.height, line_height * 2):
            row_idx = (y - self.rect.y) // (line_height * 2)
            wave_idx = min(row_idx * len(waveform) // num_rows, len(waveform) - 1)
            val = waveform[wave_idx]
            width = int(abs(val) * self.rect.width * 0.8)
            x = self.rect.centerx - width // 2

            pygame.draw.rect(surface, self.colors['foreground'],
                           (x, y, width, line_height))


class RetroTV(BaseVisualization):
    """38. 레트로 TV"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        # TV 프레임
        frame_color = self.colors['dim']
        pygame.draw.rect(surface, frame_color, self.rect, 4)

        # 내부 영역
        inner = self.rect.inflate(-20, -20)

        # 스캔 효과
        scan_y = int((self.time * 100) % inner.height)
        pygame.draw.line(surface, self.colors['bright'],
                        (inner.x, inner.y + scan_y),
                        (inner.x + inner.width, inner.y + scan_y), 1)

        # 파형 표시
        if len(waveform) > 1:
            cy = inner.centery
            points = []
            for i, val in enumerate(waveform[::2]):
                x = inner.x + int(i * inner.width / (len(waveform) // 2))
                y = cy - int(val * inner.height * 0.3)
                points.append((x, y))

            if len(points) > 1:
                pygame.draw.lines(surface, self.colors['foreground'], False, points, 2)


class CRTMonitor(BaseVisualization):
    """39. CRT 모니터"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        cx = self.rect.centerx
        cy = self.rect.centery

        # 곡면 효과 (간단한 왜곡)
        if len(waveform) > 1:
            points = []
            for i, val in enumerate(waveform):
                x = self.rect.x + int(i * self.rect.width / len(waveform))
                y = cy - int(val * self.rect.height * 0.4)

                # 배럴 왜곡
                dx = (x - cx) / self.rect.width
                dy = (y - cy) / self.rect.height
                distort = 1 + 0.1 * (dx * dx + dy * dy)
                x = cx + int((x - cx) * distort)
                y = cy + int((y - cy) * distort)

                points.append((x, y))

            if len(points) > 1:
                pygame.draw.lines(surface, self.colors['bright'], False, points, 2)

        # 스캔라인 오버레이
        for y in range(self.rect.y, self.rect.y + self.rect.height, 3):
            pygame.draw.line(surface, (0, 0, 0),
                           (self.rect.x, y), (self.rect.x + self.rect.width, y))


class PixelArt(BaseVisualization):
    """40. 픽셀 아트"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(spectrum) < 1:
            return

        pixel_size = 8
        cols = self.rect.width // pixel_size
        rows = self.rect.height // pixel_size

        for col in range(min(cols, len(spectrum))):
            val = spectrum[col] if col < len(spectrum) else 0
            active_rows = int(val * rows)

            for row in range(active_rows):
                x = self.rect.x + col * pixel_size
                y = self.rect.y + self.rect.height - (row + 1) * pixel_size

                # 픽셀 색상 (높이에 따라 변화)
                intensity = row / rows
                color = self._get_pixel_color(intensity)

                pygame.draw.rect(surface, color,
                               (x, y, pixel_size - 1, pixel_size - 1))

    def _get_pixel_color(self, intensity):
        if intensity < 0.6:
            return self.colors['foreground']
        elif intensity < 0.8:
            return self.colors['warning']
        else:
            return self.colors['bright']


# ==================== 과학적 시각화 ====================

class FrequencyBands(BaseVisualization):
    """41. 주파수 대역"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(spectrum) < 1:
            return

        bands = [
            ("SUB", 0, 4),
            ("BASS", 4, 8),
            ("LOW-MID", 8, 16),
            ("MID", 16, 32),
            ("HIGH-MID", 32, 48),
            ("HIGH", 48, 64),
        ]

        band_height = self.rect.height // len(bands)

        for i, (name, start, end) in enumerate(bands):
            end = min(end, len(spectrum))
            if start < len(spectrum):
                val = np.mean(spectrum[start:end])
            else:
                val = 0

            y = self.rect.y + i * band_height
            bar_width = int(val * self.rect.width * 0.8)

            # 바 그리기
            pygame.draw.rect(surface, self.colors['foreground'],
                           (self.rect.x, y + 2, bar_width, band_height - 4))

            # 레이블
            font = kwargs.get('font')
            if font:
                text = font.render(name, self.colors['dim'])
                surface.blit(text, (self.rect.x + 5, y + 5))


class Chromagram(BaseVisualization):
    """42. 크로마그램"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(spectrum) < 12:
            return

        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        bar_width = self.rect.width // 12

        # 스펙트럼을 12개 노트로 매핑 (단순화)
        chroma = np.zeros(12)
        for i, val in enumerate(spectrum):
            note_idx = i % 12
            chroma[note_idx] += val

        chroma = chroma / (len(spectrum) // 12 + 1)

        for i, val in enumerate(chroma):
            x = self.rect.x + i * bar_width
            h = int(val * self.rect.height * 0.9)
            y = self.rect.y + self.rect.height - h

            pygame.draw.rect(surface, self.colors['foreground'],
                           (x, y, bar_width - 2, h))

            # 노트 레이블
            font = kwargs.get('font')
            if font:
                text = font.render(notes[i], self.colors['dim'])
                surface.blit(text, (x + 2, self.rect.y + self.rect.height - 15))


class Sonogram(BaseVisualization):
    """43. 소노그램"""

    def __init__(self, rect: Rect, colors: dict):
        super().__init__(rect, colors)
        self.history = []
        self.max_history = rect.width

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(spectrum) < 1:
            return

        # 히스토리 추가
        self.history.append(spectrum.copy())
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # 각 열 렌더링
        for x_idx, col in enumerate(self.history):
            x = self.rect.x + x_idx

            for y_idx, val in enumerate(col):
                if y_idx >= self.rect.height:
                    break

                y = self.rect.y + self.rect.height - y_idx - 1
                intensity = int(val * 255)
                color = (0, intensity, 0)

                surface.set_at((x, y), color)


class Wavefunction(BaseVisualization):
    """44. 파동 함수"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 2:
            return

        cy = self.rect.centery

        # 실수부와 허수부 (FFT 기반)
        fft = np.fft.fft(waveform)
        real = np.real(fft)[:len(waveform) // 2]
        imag = np.imag(fft)[:len(waveform) // 2]

        # 정규화
        max_val = max(np.max(np.abs(real)), np.max(np.abs(imag)), 1)
        real = real / max_val
        imag = imag / max_val

        # 실수부 그리기
        points_real = []
        for i, val in enumerate(real):
            x = self.rect.x + int(i * self.rect.width / len(real))
            y = cy - int(val * self.rect.height * 0.3)
            points_real.append((x, y))

        # 허수부 그리기
        points_imag = []
        for i, val in enumerate(imag):
            x = self.rect.x + int(i * self.rect.width / len(imag))
            y = cy - int(val * self.rect.height * 0.3)
            points_imag.append((x, y))

        if len(points_real) > 1:
            pygame.draw.lines(surface, self.colors['foreground'], False, points_real, 2)
        if len(points_imag) > 1:
            pygame.draw.lines(surface, self.colors['dim'], False, points_imag, 1)


class EnergyField(BaseVisualization):
    """45. 에너지 필드"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        cx = self.rect.centerx
        cy = self.rect.centery

        energy = np.mean(np.abs(waveform)) if len(waveform) > 0 else 0.5
        max_radius = min(self.rect.width, self.rect.height) * 0.4

        # 에너지 등고선
        for i in range(10):
            radius = max_radius * (i + 1) / 10 * (0.5 + energy * 0.5)
            # 불규칙한 원
            points = []
            for angle_idx in range(36):
                angle = angle_idx * math.pi / 18 + self.time
                noise = 0.1 * math.sin(angle * 5 + self.time * 3)
                r = radius * (1 + noise * energy)

                x = cx + int(r * math.cos(angle))
                y = cy + int(r * math.sin(angle))
                points.append((x, y))

            points.append(points[0])

            alpha = 1.0 - i * 0.1
            color = tuple(int(c * alpha) for c in self.colors['foreground'])
            pygame.draw.lines(surface, color, False, points, 1)


# ==================== 공간 시각화 ====================

class StereoField(BaseVisualization):
    """46. 스테레오 필드"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 2:
            return

        cx = self.rect.centerx
        cy = self.rect.centery
        scale = min(self.rect.width, self.rect.height) * 0.4

        # 그리드
        pygame.draw.line(surface, self.colors['dim'],
                        (cx, self.rect.y), (cx, self.rect.y + self.rect.height))
        pygame.draw.line(surface, self.colors['dim'],
                        (self.rect.x, cy), (self.rect.x + self.rect.width, cy))

        half = len(waveform) // 2
        for i in range(0, half, 2):
            l = waveform[i]
            r = waveform[i + half] if i + half < len(waveform) else l

            x = cx + int((l - r) * scale)  # 스테레오 폭
            y = cy - int((l + r) / 2 * scale)  # 모노 레벨

            pygame.draw.circle(surface, self.colors['foreground'], (x, y), 1)


class Surround(BaseVisualization):
    """47. 서라운드 시각화"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        cx = self.rect.centerx
        cy = self.rect.centery
        radius = min(self.rect.width, self.rect.height) * 0.35

        # 5.1 채널 위치 표시
        channels = [
            ("FL", -0.7, -0.5),
            ("FR", 0.7, -0.5),
            ("C", 0, -0.3),
            ("LFE", 0, 0.3),
            ("SL", -0.9, 0.5),
            ("SR", 0.9, 0.5),
        ]

        energy = np.mean(np.abs(waveform)) if len(waveform) > 0 else 0.5

        for name, dx, dy in channels:
            x = cx + int(dx * radius)
            y = cy + int(dy * radius)

            # 채널 레벨 (시뮬레이션)
            level = energy * (0.5 + random.random() * 0.5)
            size = int(10 + level * 20)

            pygame.draw.circle(surface, self.colors['dim'], (x, y), size, 1)
            pygame.draw.circle(surface, self.colors['foreground'], (x, y), int(size * level))

            font = kwargs.get('font')
            if font:
                text = font.render(name, self.colors['dim'])
                surface.blit(text, (x - 10, y + size + 5))


class Depth3D(BaseVisualization):
    """48. 3D 깊이감"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(spectrum) < 1:
            return

        cx = self.rect.centerx
        cy = self.rect.centery

        # 3D 바 효과
        bar_count = min(32, len(spectrum))
        bar_width = 15
        depth_offset = 3

        for i in range(bar_count):
            val = spectrum[i] if i < len(spectrum) else 0
            h = int(val * self.rect.height * 0.6)

            base_x = cx - (bar_count * bar_width) // 2 + i * bar_width
            base_y = cy + self.rect.height // 4

            # 3D 효과를 위한 옆면
            points_side = [
                (base_x + bar_width, base_y - h),
                (base_x + bar_width + depth_offset, base_y - h - depth_offset),
                (base_x + bar_width + depth_offset, base_y - depth_offset),
                (base_x + bar_width, base_y),
            ]
            pygame.draw.polygon(surface, self.colors['dim'], points_side)

            # 윗면
            points_top = [
                (base_x, base_y - h),
                (base_x + depth_offset, base_y - h - depth_offset),
                (base_x + bar_width + depth_offset, base_y - h - depth_offset),
                (base_x + bar_width, base_y - h),
            ]
            pygame.draw.polygon(surface, self.colors['bright'], points_top)

            # 앞면
            pygame.draw.rect(surface, self.colors['foreground'],
                           (base_x, base_y - h, bar_width - 1, h))


# ==================== 실험적 시각화 ====================

class Glitch(BaseVisualization):
    """49. 글리치"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 1:
            return

        energy = np.mean(np.abs(waveform))

        # 기본 파형
        cy = self.rect.centery
        points = []
        for i, val in enumerate(waveform):
            x = self.rect.x + int(i * self.rect.width / len(waveform))
            y = cy - int(val * self.rect.height * 0.4)
            points.append((x, y))

        if len(points) > 1:
            pygame.draw.lines(surface, self.colors['foreground'], False, points, 2)

        # 글리치 효과
        if energy > 0.3:
            for _ in range(int(energy * 10)):
                glitch_y = random.randint(self.rect.y, self.rect.y + self.rect.height)
                glitch_h = random.randint(2, 10)
                shift = random.randint(-20, 20)

                # 라인 복사 및 시프트
                src_rect = Rect(self.rect.x, glitch_y, self.rect.width, glitch_h)
                if src_rect.bottom <= self.rect.bottom:
                    try:
                        region = surface.subsurface(src_rect).copy()
                        surface.blit(region, (self.rect.x + shift, glitch_y))
                    except:
                        pass


class DataMosh(BaseVisualization):
    """50. 데이터 모싱"""

    def __init__(self, rect: Rect, colors: dict):
        super().__init__(rect, colors)
        self.prev_waveform = None

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        if len(waveform) < 2:
            return

        cy = self.rect.centery

        # 이전 프레임과 혼합
        if self.prev_waveform is not None and len(self.prev_waveform) == len(waveform):
            mixed = waveform * 0.7 + self.prev_waveform * 0.3

            # 불규칙한 블렌딩
            for i in range(len(mixed)):
                if random.random() < 0.1:
                    mixed[i] = self.prev_waveform[i]
        else:
            mixed = waveform

        self.prev_waveform = waveform.copy()

        # 렌더링
        points = []
        for i, val in enumerate(mixed):
            x = self.rect.x + int(i * self.rect.width / len(mixed))
            y = cy - int(val * self.rect.height * 0.4)
            points.append((x, y))

        if len(points) > 1:
            pygame.draw.lines(surface, self.colors['foreground'], False, points, 2)


class Fractal(BaseVisualization):
    """51. 프랙탈"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        cx = self.rect.centerx
        cy = self.rect.centery

        energy = np.mean(np.abs(waveform)) if len(waveform) > 0 else 0.5
        depth = min(6, int(3 + energy * 4))

        self._draw_branch(surface, cx, self.rect.y + self.rect.height,
                         -math.pi / 2, 80 * (0.5 + energy * 0.5), depth)

    def _draw_branch(self, surface, x, y, angle, length, depth):
        if depth == 0 or length < 2:
            return

        end_x = x + int(length * math.cos(angle))
        end_y = y + int(length * math.sin(angle))

        alpha = depth / 6
        color = tuple(int(c * alpha) for c in self.colors['foreground'])
        pygame.draw.line(surface, color, (int(x), int(y)), (end_x, end_y), max(1, depth // 2))

        # 분기
        new_length = length * 0.7
        spread = 0.4 + self.time * 0.1

        self._draw_branch(surface, end_x, end_y, angle - spread, new_length, depth - 1)
        self._draw_branch(surface, end_x, end_y, angle + spread, new_length, depth - 1)


class NeuralNet(BaseVisualization):
    """52. 신경망"""

    def render(self, surface: Surface, waveform: np.ndarray,
               spectrum: np.ndarray, **kwargs):
        layers = [8, 12, 12, 8]
        layer_spacing = self.rect.width // (len(layers) + 1)

        positions = []

        for layer_idx, node_count in enumerate(layers):
            layer_x = self.rect.x + (layer_idx + 1) * layer_spacing
            node_spacing = self.rect.height // (node_count + 1)

            layer_positions = []
            for node_idx in range(node_count):
                y = self.rect.y + (node_idx + 1) * node_spacing
                layer_positions.append((layer_x, y))
            positions.append(layer_positions)

        # 연결선 그리기
        energy = np.mean(np.abs(waveform)) if len(waveform) > 0 else 0.5

        for layer_idx in range(len(positions) - 1):
            for pos1 in positions[layer_idx]:
                for pos2 in positions[layer_idx + 1]:
                    alpha = 0.2 + energy * 0.3
                    color = tuple(int(c * alpha) for c in self.colors['dim'])
                    pygame.draw.line(surface, color, pos1, pos2, 1)

        # 노드 그리기
        for layer_idx, layer in enumerate(positions):
            for node_idx, pos in enumerate(layer):
                # 활성화 (스펙트럼 기반)
                spec_idx = (layer_idx * 16 + node_idx) % max(1, len(spectrum))
                activation = spectrum[spec_idx] if spec_idx < len(spectrum) else 0.5

                size = int(3 + activation * 5)
                pygame.draw.circle(surface, self.colors['foreground'], pos, size)


# ==================== 시각화 레지스트리 ====================

VISUALIZATIONS = {
    # 파형 (01-08)
    "waveform_line": (WaveformLine, VisualizationInfo("waveform_line", "Line Waveform", "선 파형", VisualizationCategory.WAVEFORM, "기본 선 파형")),
    "waveform_filled": (WaveformFilled, VisualizationInfo("waveform_filled", "Filled Waveform", "채워진 파형", VisualizationCategory.WAVEFORM, "채워진 파형")),
    "waveform_mirror": (WaveformMirror, VisualizationInfo("waveform_mirror", "Mirror Waveform", "미러 파형", VisualizationCategory.WAVEFORM, "위아래 대칭 파형")),
    "waveform_bars": (WaveformBars, VisualizationInfo("waveform_bars", "Bar Waveform", "바 파형", VisualizationCategory.WAVEFORM, "바 형태 파형")),
    "waveform_dots": (WaveformDots, VisualizationInfo("waveform_dots", "Dot Waveform", "점 파형", VisualizationCategory.WAVEFORM, "점으로 표현된 파형")),
    "waveform_gradient": (WaveformGradient, VisualizationInfo("waveform_gradient", "Gradient Waveform", "그라데이션 파형", VisualizationCategory.WAVEFORM, "색상 그라데이션 파형")),
    "waveform_circular": (WaveformCircular, VisualizationInfo("waveform_circular", "Circular Waveform", "원형 파형", VisualizationCategory.WAVEFORM, "원형으로 배치된 파형")),
    "waveform_spiral": (WaveformSpiral, VisualizationInfo("waveform_spiral", "Spiral Waveform", "나선형 파형", VisualizationCategory.WAVEFORM, "나선형 파형")),

    # 스펙트럼 (09-16)
    "spectrum_bars": (SpectrumBars, VisualizationInfo("spectrum_bars", "Spectrum Bars", "스펙트럼 바", VisualizationCategory.SPECTRUM, "주파수 스펙트럼 바")),
    "spectrum_mirror": (SpectrumMirror, VisualizationInfo("spectrum_mirror", "Mirror Spectrum", "미러 스펙트럼", VisualizationCategory.SPECTRUM, "위아래 대칭 스펙트럼")),
    "spectrum_line": (SpectrumLine, VisualizationInfo("spectrum_line", "Line Spectrum", "선 스펙트럼", VisualizationCategory.SPECTRUM, "선으로 연결된 스펙트럼")),
    "spectrum_filled": (SpectrumFilled, VisualizationInfo("spectrum_filled", "Filled Spectrum", "채워진 스펙트럼", VisualizationCategory.SPECTRUM, "채워진 스펙트럼")),
    "spectrum_circular": (SpectrumCircular, VisualizationInfo("spectrum_circular", "Circular Spectrum", "원형 스펙트럼", VisualizationCategory.SPECTRUM, "원형 스펙트럼")),
    "spectrum_radial": (SpectrumRadial, VisualizationInfo("spectrum_radial", "Radial Spectrum", "방사형 스펙트럼", VisualizationCategory.SPECTRUM, "방사형 스펙트럼")),
    "spectrum_waterfall": (SpectrumWaterfall, VisualizationInfo("spectrum_waterfall", "Waterfall", "폭포수", VisualizationCategory.SPECTRUM, "시간축 스펙트럼")),
    "spectrogram_3d": (Spectrogram3D, VisualizationInfo("spectrogram_3d", "3D Spectrogram", "3D 스펙트로그램", VisualizationCategory.SPECTRUM, "입체적 스펙트로그램")),

    # 미터 (17-20)
    "vu_meter": (VUMeter, VisualizationInfo("vu_meter", "VU Meter", "VU 미터", VisualizationCategory.METER, "볼륨 유닛 미터")),
    "level_meter": (LevelMeter, VisualizationInfo("level_meter", "Level Meter", "레벨 미터", VisualizationCategory.METER, "세그먼트 레벨 미터")),
    "stereo_meter": (StereoMeter, VisualizationInfo("stereo_meter", "Stereo Meter", "스테레오 미터", VisualizationCategory.METER, "좌우 채널 미터")),
    "peak_meter": (PeakMeter, VisualizationInfo("peak_meter", "Peak Meter", "피크 미터", VisualizationCategory.METER, "피크 히스토리")),

    # 스코프 (21-24)
    "oscilloscope": (Oscilloscope, VisualizationInfo("oscilloscope", "Oscilloscope", "오실로스코프", VisualizationCategory.SCOPE, "오실로스코프")),
    "xy_scope": (XYScope, VisualizationInfo("xy_scope", "XY Scope", "XY 스코프", VisualizationCategory.SCOPE, "리사주 패턴")),
    "vectorscope": (Vectorscope, VisualizationInfo("vectorscope", "Vectorscope", "벡터스코프", VisualizationCategory.SCOPE, "벡터스코프")),
    "phase_scope": (PhaseScope, VisualizationInfo("phase_scope", "Phase Scope", "위상 스코프", VisualizationCategory.SCOPE, "위상 상관 표시")),

    # 패턴 (25-30)
    "matrix_rain": (MatrixRain, VisualizationInfo("matrix_rain", "Matrix Rain", "매트릭스 레인", VisualizationCategory.PATTERN, "매트릭스 스타일")),
    "ascii_wave": (ASCIIWave, VisualizationInfo("ascii_wave", "ASCII Wave", "ASCII 파형", VisualizationCategory.PATTERN, "문자로 표현된 파형")),
    "block_wave": (BlockWave, VisualizationInfo("block_wave", "Block Wave", "블록 파형", VisualizationCategory.PATTERN, "블록으로 표현된 파형")),
    "particles": (Particles, VisualizationInfo("particles", "Particles", "파티클", VisualizationCategory.PATTERN, "파티클 시스템")),
    "starfield": (Starfield, VisualizationInfo("starfield", "Starfield", "스타필드", VisualizationCategory.PATTERN, "별 필드")),
    "tunnel": (Tunnel, VisualizationInfo("tunnel", "Tunnel", "터널", VisualizationCategory.PATTERN, "터널 효과")),

    # 아티스틱 (31-36)
    "kaleidoscope": (Kaleidoscope, VisualizationInfo("kaleidoscope", "Kaleidoscope", "만화경", VisualizationCategory.ARTISTIC, "만화경 패턴")),
    "mandala": (Mandala, VisualizationInfo("mandala", "Mandala", "만다라", VisualizationCategory.ARTISTIC, "만다라 패턴")),
    "flower_pattern": (FlowerPattern, VisualizationInfo("flower_pattern", "Flower Pattern", "꽃 패턴", VisualizationCategory.ARTISTIC, "꽃 형태 패턴")),
    "geometric_shapes": (GeometricShapes, VisualizationInfo("geometric_shapes", "Geometric Shapes", "기하학 도형", VisualizationCategory.ARTISTIC, "회전하는 다각형")),
    "sacred_geometry": (SacredGeometry, VisualizationInfo("sacred_geometry", "Sacred Geometry", "신성 기하학", VisualizationCategory.ARTISTIC, "생명의 꽃")),
    "wave_rings": (WaveRings, VisualizationInfo("wave_rings", "Wave Rings", "파동 링", VisualizationCategory.ARTISTIC, "확장되는 원")),

    # 레트로 (37-40)
    "scanlines": (Scanlines, VisualizationInfo("scanlines", "Scanlines", "스캔라인", VisualizationCategory.RETRO, "스캔라인 효과")),
    "retro_tv": (RetroTV, VisualizationInfo("retro_tv", "Retro TV", "레트로 TV", VisualizationCategory.RETRO, "레트로 TV 스타일")),
    "crt_monitor": (CRTMonitor, VisualizationInfo("crt_monitor", "CRT Monitor", "CRT 모니터", VisualizationCategory.RETRO, "CRT 왜곡 효과")),
    "pixel_art": (PixelArt, VisualizationInfo("pixel_art", "Pixel Art", "픽셀 아트", VisualizationCategory.RETRO, "픽셀 아트 스타일")),

    # 과학적 (41-45)
    "frequency_bands": (FrequencyBands, VisualizationInfo("frequency_bands", "Frequency Bands", "주파수 대역", VisualizationCategory.SCIENTIFIC, "주파수 대역별 분석")),
    "chromagram": (Chromagram, VisualizationInfo("chromagram", "Chromagram", "크로마그램", VisualizationCategory.SCIENTIFIC, "음계 기반 분석")),
    "sonogram": (Sonogram, VisualizationInfo("sonogram", "Sonogram", "소노그램", VisualizationCategory.SCIENTIFIC, "시간-주파수 표시")),
    "wavefunction": (Wavefunction, VisualizationInfo("wavefunction", "Wavefunction", "파동 함수", VisualizationCategory.SCIENTIFIC, "FFT 실수/허수부")),
    "energy_field": (EnergyField, VisualizationInfo("energy_field", "Energy Field", "에너지 필드", VisualizationCategory.SCIENTIFIC, "에너지 등고선")),

    # 공간 (46-48)
    "stereo_field": (StereoField, VisualizationInfo("stereo_field", "Stereo Field", "스테레오 필드", VisualizationCategory.SPATIAL, "스테레오 이미지")),
    "surround": (Surround, VisualizationInfo("surround", "Surround", "서라운드", VisualizationCategory.SPATIAL, "5.1 서라운드")),
    "depth_3d": (Depth3D, VisualizationInfo("depth_3d", "3D Depth", "3D 깊이감", VisualizationCategory.SPATIAL, "입체적 바")),

    # 실험적 (49-52)
    "glitch": (Glitch, VisualizationInfo("glitch", "Glitch", "글리치", VisualizationCategory.EXPERIMENTAL, "글리치 효과")),
    "data_mosh": (DataMosh, VisualizationInfo("data_mosh", "Data Mosh", "데이터 모싱", VisualizationCategory.EXPERIMENTAL, "데이터 모싱")),
    "fractal": (Fractal, VisualizationInfo("fractal", "Fractal Tree", "프랙탈 트리", VisualizationCategory.EXPERIMENTAL, "프랙탈 나무")),
    "neural_net": (NeuralNet, VisualizationInfo("neural_net", "Neural Network", "신경망", VisualizationCategory.EXPERIMENTAL, "신경망 시각화")),
}


def get_visualization_list() -> List[VisualizationInfo]:
    """시각화 목록 반환"""
    return [info for _, info in VISUALIZATIONS.values()]


def get_visualization_by_category(category: VisualizationCategory) -> List[VisualizationInfo]:
    """카테고리별 시각화 목록"""
    return [info for _, info in VISUALIZATIONS.values() if info.category == category]


def create_visualization(viz_id: str, rect: Rect, colors: dict) -> Optional[BaseVisualization]:
    """시각화 인스턴스 생성"""
    if viz_id in VISUALIZATIONS:
        viz_class, _ = VISUALIZATIONS[viz_id]
        return viz_class(rect, colors)
    return None
