"""
군사용 메인프레임 스타일 GUI 애플리케이션

80~90년대 군사용 메인프레임/터미널 스타일의 레트로 GUI.
CRT 효과, 인광 잔상, 스캔라인 등을 구현합니다.
"""

import sys
import time
import math
import random
from pathlib import Path
from typing import Optional, Tuple, List, Callable
from dataclasses import dataclass
from enum import Enum

import numpy as np

try:
    import pygame
    from pygame import Surface, Rect
    from pygame.locals import *
except ImportError:
    print("pygame이 설치되어 있지 않습니다.")
    print("설치: pip install pygame")
    sys.exit(1)


class PhosphorColor(Enum):
    """인광체 색상 (CRT 모니터 타입)"""
    GREEN = "green"      # P1 - 클래식 그린
    AMBER = "amber"      # P3 - 앰버
    WHITE = "white"      # P4 - 화이트
    BLUE = "blue"        # 군사용 블루


@dataclass
class ColorScheme:
    """색상 스킴"""
    background: Tuple[int, int, int]
    foreground: Tuple[int, int, int]
    dim: Tuple[int, int, int]
    bright: Tuple[int, int, int]
    highlight: Tuple[int, int, int]
    warning: Tuple[int, int, int]
    error: Tuple[int, int, int]
    border: Tuple[int, int, int]


# 인광체 색상별 스킴
PHOSPHOR_SCHEMES = {
    PhosphorColor.GREEN: ColorScheme(
        background=(0, 10, 0),
        foreground=(0, 200, 0),
        dim=(0, 80, 0),
        bright=(0, 255, 0),
        highlight=(100, 255, 100),
        warning=(200, 200, 0),
        error=(255, 50, 50),
        border=(0, 150, 0),
    ),
    PhosphorColor.AMBER: ColorScheme(
        background=(10, 5, 0),
        foreground=(255, 176, 0),
        dim=(100, 70, 0),
        bright=(255, 200, 50),
        highlight=(255, 220, 100),
        warning=(255, 255, 0),
        error=(255, 100, 100),
        border=(200, 140, 0),
    ),
    PhosphorColor.WHITE: ColorScheme(
        background=(5, 5, 10),
        foreground=(200, 200, 220),
        dim=(80, 80, 100),
        bright=(255, 255, 255),
        highlight=(220, 220, 255),
        warning=(255, 255, 0),
        error=(255, 100, 100),
        border=(150, 150, 170),
    ),
    PhosphorColor.BLUE: ColorScheme(
        background=(0, 0, 15),
        foreground=(100, 150, 255),
        dim=(30, 50, 100),
        bright=(150, 200, 255),
        highlight=(200, 220, 255),
        warning=(255, 255, 0),
        error=(255, 50, 50),
        border=(80, 120, 200),
    ),
}


class CRTEffect:
    """CRT 포스트 프로세싱 효과"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.scanline_surface = self._create_scanlines()
        self.vignette_surface = self._create_vignette()
        self.noise_intensity = 0.02
        self.phosphor_persistence = 0.85
        self.previous_frame: Optional[Surface] = None
        self.flicker_amount = 0.02
        self.curvature = 0.03

    def _create_scanlines(self) -> Surface:
        """스캔라인 오버레이 생성"""
        surface = Surface((self.width, self.height), SRCALPHA)
        for y in range(0, self.height, 2):
            pygame.draw.line(surface, (0, 0, 0, 60), (0, y), (self.width, y))
        return surface

    def _create_vignette(self) -> Surface:
        """비네트 효과 생성"""
        surface = Surface((self.width, self.height), SRCALPHA)
        cx, cy = self.width // 2, self.height // 2
        max_dist = math.sqrt(cx**2 + cy**2)

        for y in range(self.height):
            for x in range(self.width):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                alpha = int((dist / max_dist) ** 2 * 150)
                surface.set_at((x, y), (0, 0, 0, min(alpha, 200)))

        return surface

    def apply(self, surface: Surface) -> Surface:
        """CRT 효과 적용"""
        result = surface.copy()

        # 인광 잔상 (이전 프레임과 블렌딩)
        if self.previous_frame is not None:
            result.blit(self.previous_frame, (0, 0), special_flags=BLEND_ADD)
            # 잔상 페이드
            fade = Surface(result.get_size())
            fade.fill((int(255 * (1 - self.phosphor_persistence)),) * 3)
            result.blit(fade, (0, 0), special_flags=BLEND_RGB_SUB)

        # 플리커 효과
        if random.random() < 0.1:
            flicker = 1.0 - random.random() * self.flicker_amount
            darken = Surface(result.get_size())
            darken.fill((int(255 * (1 - flicker)),) * 3)
            result.blit(darken, (0, 0), special_flags=BLEND_RGB_SUB)

        # 노이즈
        if self.noise_intensity > 0:
            noise = Surface(result.get_size())
            pixels = pygame.surfarray.pixels3d(noise)
            noise_data = np.random.randint(
                0, int(255 * self.noise_intensity),
                (self.width, self.height, 3),
                dtype=np.uint8
            )
            pixels[:] = noise_data
            del pixels
            result.blit(noise, (0, 0), special_flags=BLEND_ADD)

        # 스캔라인
        result.blit(self.scanline_surface, (0, 0))

        # 비네트
        result.blit(self.vignette_surface, (0, 0))

        # 다음 프레임을 위해 저장 (잔상용)
        self.previous_frame = result.copy()

        return result


class TerminalFont:
    """터미널 스타일 폰트 렌더러"""

    def __init__(self, size: int = 16):
        pygame.font.init()

        # 모노스페이스 폰트 찾기
        font_names = [
            "Consolas", "Courier New", "Lucida Console",
            "Monaco", "DejaVu Sans Mono", "monospace"
        ]

        self.font = None
        for name in font_names:
            try:
                self.font = pygame.font.SysFont(name, size)
                break
            except:
                continue

        if self.font is None:
            self.font = pygame.font.Font(None, size)

        self.char_width = self.font.size("M")[0]
        self.char_height = self.font.get_linesize()

    def render(self, text: str, color: Tuple[int, int, int],
               antialias: bool = True) -> Surface:
        """텍스트 렌더링"""
        return self.font.render(text, antialias, color)

    def render_multiline(self, text: str, color: Tuple[int, int, int],
                         max_width: int = 0) -> Surface:
        """여러 줄 텍스트 렌더링"""
        lines = text.split('\n')

        if max_width > 0:
            wrapped_lines = []
            chars_per_line = max_width // self.char_width
            for line in lines:
                while len(line) > chars_per_line:
                    wrapped_lines.append(line[:chars_per_line])
                    line = line[chars_per_line:]
                wrapped_lines.append(line)
            lines = wrapped_lines

        height = len(lines) * self.char_height
        width = max(self.font.size(line)[0] for line in lines) if lines else 0

        surface = Surface((width, height), SRCALPHA)
        for i, line in enumerate(lines):
            rendered = self.font.render(line, True, color)
            surface.blit(rendered, (0, i * self.char_height))

        return surface


class Panel:
    """군사 스타일 패널 위젯"""

    def __init__(self, rect: Rect, title: str, scheme: ColorScheme):
        self.rect = rect
        self.title = title
        self.scheme = scheme
        self.content_rect = Rect(
            rect.x + 2, rect.y + 20,
            rect.width - 4, rect.height - 22
        )

    def draw(self, surface: Surface, font: TerminalFont):
        """패널 그리기"""
        # 배경
        pygame.draw.rect(surface, self.scheme.background, self.rect)

        # 테두리 (이중선)
        pygame.draw.rect(surface, self.scheme.border, self.rect, 2)
        inner = self.rect.inflate(-4, -4)
        pygame.draw.rect(surface, self.scheme.dim, inner, 1)

        # 타이틀 바
        title_bar = Rect(self.rect.x, self.rect.y, self.rect.width, 18)
        pygame.draw.rect(surface, self.scheme.dim, title_bar)
        pygame.draw.line(
            surface, self.scheme.border,
            (self.rect.x, self.rect.y + 18),
            (self.rect.x + self.rect.width, self.rect.y + 18)
        )

        # 타이틀 텍스트
        title_text = font.render(f" {self.title} ", self.scheme.bright)
        surface.blit(title_text, (self.rect.x + 4, self.rect.y + 2))


class StatusBar:
    """상태 바"""

    def __init__(self, rect: Rect, scheme: ColorScheme):
        self.rect = rect
        self.scheme = scheme
        self.items: List[Tuple[str, str]] = []

    def set_items(self, items: List[Tuple[str, str]]):
        """상태 항목 설정 [(label, value), ...]"""
        self.items = items

    def draw(self, surface: Surface, font: TerminalFont):
        """상태 바 그리기"""
        pygame.draw.rect(surface, self.scheme.dim, self.rect)
        pygame.draw.line(
            surface, self.scheme.border,
            (self.rect.x, self.rect.y),
            (self.rect.x + self.rect.width, self.rect.y)
        )

        x = self.rect.x + 10
        for label, value in self.items:
            text = f"{label}: {value}"
            rendered = font.render(text, self.scheme.foreground)
            surface.blit(rendered, (x, self.rect.y + 3))
            x += rendered.get_width() + 30

            # 구분선
            pygame.draw.line(
                surface, self.scheme.border,
                (x - 15, self.rect.y + 2),
                (x - 15, self.rect.y + self.rect.height - 2)
            )


class VisualizerPanel:
    """오디오 시각화 패널"""

    def __init__(self, rect: Rect, scheme: ColorScheme):
        self.rect = rect
        self.scheme = scheme
        self.waveform_data = np.zeros(100)
        self.spectrum_data = np.zeros(64)
        self.mode = "waveform"  # waveform, spectrum, scope

    def set_waveform(self, data: np.ndarray):
        """파형 데이터 설정"""
        self.waveform_data = data

    def set_spectrum(self, data: np.ndarray):
        """스펙트럼 데이터 설정"""
        self.spectrum_data = data

    def draw(self, surface: Surface):
        """시각화 그리기"""
        pygame.draw.rect(surface, self.scheme.background, self.rect)
        pygame.draw.rect(surface, self.scheme.border, self.rect, 1)

        if self.mode == "waveform":
            self._draw_waveform(surface)
        elif self.mode == "spectrum":
            self._draw_spectrum(surface)
        elif self.mode == "scope":
            self._draw_scope(surface)

    def _draw_waveform(self, surface: Surface):
        """파형 그리기"""
        if len(self.waveform_data) < 2:
            return

        cx = self.rect.x + self.rect.width // 2
        cy = self.rect.y + self.rect.height // 2

        # 중앙선
        pygame.draw.line(
            surface, self.scheme.dim,
            (self.rect.x, cy), (self.rect.x + self.rect.width, cy)
        )

        # 파형
        points = []
        for i, val in enumerate(self.waveform_data):
            x = self.rect.x + int(i * self.rect.width / len(self.waveform_data))
            y = cy - int(val * self.rect.height * 0.4)
            points.append((x, y))

        if len(points) > 1:
            pygame.draw.lines(surface, self.scheme.bright, False, points, 2)

    def _draw_spectrum(self, surface: Surface):
        """스펙트럼 그리기"""
        if len(self.spectrum_data) < 1:
            return

        bar_width = max(1, self.rect.width // len(self.spectrum_data) - 1)

        for i, val in enumerate(self.spectrum_data):
            x = self.rect.x + i * (bar_width + 1)
            height = int(val * self.rect.height * 0.9)
            y = self.rect.y + self.rect.height - height

            # 그라데이션 효과
            color = self.scheme.foreground
            if val > 0.7:
                color = self.scheme.bright
            elif val > 0.9:
                color = self.scheme.highlight

            pygame.draw.rect(surface, color, (x, y, bar_width, height))

    def _draw_scope(self, surface: Surface):
        """오실로스코프 스타일"""
        cx = self.rect.x + self.rect.width // 2
        cy = self.rect.y + self.rect.height // 2

        # 그리드
        for i in range(0, self.rect.width, 20):
            pygame.draw.line(
                surface, self.scheme.dim,
                (self.rect.x + i, self.rect.y),
                (self.rect.x + i, self.rect.y + self.rect.height)
            )
        for i in range(0, self.rect.height, 20):
            pygame.draw.line(
                surface, self.scheme.dim,
                (self.rect.x, self.rect.y + i),
                (self.rect.x + self.rect.width, self.rect.y + i)
            )

        # 파형 (녹색 발광 효과)
        if len(self.waveform_data) > 1:
            points = []
            for i, val in enumerate(self.waveform_data):
                x = self.rect.x + int(i * self.rect.width / len(self.waveform_data))
                y = cy - int(val * self.rect.height * 0.4)
                points.append((x, y))

            # 글로우 효과
            for offset in range(3, 0, -1):
                alpha = 100 - offset * 30
                glow_color = (*self.scheme.foreground[:3],)
                pygame.draw.lines(surface, glow_color, False, points, offset * 2)

            pygame.draw.lines(surface, self.scheme.bright, False, points, 2)


class MainframeApp:
    """
    군사용 메인프레임 스타일 GUI 애플리케이션

    80~90년대 군사용 터미널/메인프레임 느낌의 레트로 GUI.
    """

    def __init__(
        self,
        width: int = 1024,
        height: int = 768,
        phosphor: PhosphorColor = PhosphorColor.GREEN,
        title: str = "MAINFRAME AUDIO VISUALIZATION SYSTEM",
        crt_effects: bool = True,
    ):
        pygame.init()
        pygame.display.set_caption(f"█ {title} █")

        self.width = width
        self.height = height
        self.phosphor = phosphor
        self.scheme = PHOSPHOR_SCHEMES[phosphor]
        self.crt_effects_enabled = crt_effects

        # 디스플레이 설정
        self.screen = pygame.display.set_mode((width, height))
        self.buffer = Surface((width, height))
        self.clock = pygame.time.Clock()
        self.running = False
        self.fps = 30

        # CRT 효과
        self.crt = CRTEffect(width, height) if crt_effects else None

        # 폰트
        self.font = TerminalFont(14)
        self.font_large = TerminalFont(18)
        self.font_small = TerminalFont(12)

        # UI 컴포넌트
        self._setup_ui()

        # 상태
        self.frame_count = 0
        self.start_time = time.time()
        self.current_file = "NO FILE LOADED"
        self.system_status = "STANDBY"

        # 터미널 로그
        self.terminal_lines: List[Tuple[str, Tuple[int, int, int]]] = []
        self.max_terminal_lines = 20

        # 시뮬레이션용 데이터
        self._init_demo_data()

    def _setup_ui(self):
        """UI 컴포넌트 설정"""
        # 헤더
        self.header_rect = Rect(0, 0, self.width, 40)

        # 메인 시각화 패널
        viz_width = self.width - 320
        self.viz_panel = Panel(
            Rect(10, 50, viz_width - 20, 400),
            "■ WAVEFORM ANALYSIS ■",
            self.scheme
        )
        self.visualizer = VisualizerPanel(
            Rect(14, 72, viz_width - 28, 370),
            self.scheme
        )

        # 스펙트럼 패널
        self.spectrum_panel = Panel(
            Rect(10, 460, viz_width - 20, 200),
            "■ FREQUENCY SPECTRUM ■",
            self.scheme
        )
        self.spectrum_viz = VisualizerPanel(
            Rect(14, 482, viz_width - 28, 170),
            self.scheme
        )
        self.spectrum_viz.mode = "spectrum"

        # 사이드 패널 - 시스템 상태
        side_x = self.width - 300
        self.status_panel = Panel(
            Rect(side_x, 50, 290, 200),
            "■ SYSTEM STATUS ■",
            self.scheme
        )

        # 사이드 패널 - 파일 정보
        self.file_panel = Panel(
            Rect(side_x, 260, 290, 150),
            "■ FILE INFO ■",
            self.scheme
        )

        # 사이드 패널 - 터미널
        self.terminal_panel = Panel(
            Rect(side_x, 420, 290, 240),
            "■ SYSTEM LOG ■",
            self.scheme
        )

        # 상태 바
        self.status_bar = StatusBar(
            Rect(0, self.height - 25, self.width, 25),
            self.scheme
        )

    def _init_demo_data(self):
        """데모 데이터 초기화"""
        self.demo_phase = 0
        self.demo_waveform = np.zeros(200)
        self.demo_spectrum = np.zeros(64)

    def log(self, message: str, level: str = "INFO"):
        """터미널에 로그 추가"""
        timestamp = time.strftime("%H:%M:%S")

        color = self.scheme.foreground
        if level == "WARN":
            color = self.scheme.warning
        elif level == "ERROR":
            color = self.scheme.error
        elif level == "OK":
            color = self.scheme.bright

        line = f"[{timestamp}] {level}: {message}"
        self.terminal_lines.append((line, color))

        if len(self.terminal_lines) > self.max_terminal_lines:
            self.terminal_lines.pop(0)

    def run(self):
        """메인 루프 실행"""
        self.running = True
        self.start_time = time.time()

        self.log("SYSTEM INITIALIZATION COMPLETE", "OK")
        self.log("AUDIO SUBSYSTEM ONLINE", "OK")
        self.log("VISUALIZATION ENGINE READY", "OK")
        self.log("AWAITING INPUT...", "INFO")

        while self.running:
            self._handle_events()
            self._update()
            self._render()
            self.clock.tick(self.fps)

        pygame.quit()

    def _handle_events(self):
        """이벤트 처리"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key == K_F1:
                    self.visualizer.mode = "waveform"
                    self.log("MODE: WAVEFORM", "INFO")
                elif event.key == K_F2:
                    self.visualizer.mode = "scope"
                    self.log("MODE: OSCILLOSCOPE", "INFO")
                elif event.key == K_F3:
                    self.crt_effects_enabled = not self.crt_effects_enabled
                    status = "ENABLED" if self.crt_effects_enabled else "DISABLED"
                    self.log(f"CRT EFFECTS: {status}", "INFO")
                elif event.key == K_F4:
                    # 인광체 색상 변경
                    colors = list(PhosphorColor)
                    idx = colors.index(self.phosphor)
                    self.phosphor = colors[(idx + 1) % len(colors)]
                    self.scheme = PHOSPHOR_SCHEMES[self.phosphor]
                    self._setup_ui()
                    self.log(f"PHOSPHOR: {self.phosphor.value.upper()}", "INFO")

    def _update(self):
        """상태 업데이트"""
        self.frame_count += 1

        # 데모 데이터 생성 (실제로는 오디오 데이터 사용)
        self.demo_phase += 0.1
        t = np.linspace(0, 4 * np.pi, 200)
        self.demo_waveform = (
            np.sin(t + self.demo_phase) * 0.5 +
            np.sin(t * 2.5 + self.demo_phase * 1.3) * 0.3 +
            np.sin(t * 4.1 + self.demo_phase * 0.7) * 0.2 +
            np.random.randn(200) * 0.05
        )

        # 스펙트럼 데모
        for i in range(64):
            target = (
                0.5 * np.exp(-i / 20) *
                (1 + 0.5 * np.sin(self.demo_phase + i * 0.2))
            )
            self.demo_spectrum[i] = (
                self.demo_spectrum[i] * 0.8 + target * 0.2
            )

        self.visualizer.set_waveform(self.demo_waveform)
        self.spectrum_viz.set_spectrum(self.demo_spectrum)

        # 상태 바 업데이트
        elapsed = time.time() - self.start_time
        self.status_bar.set_items([
            ("TIME", time.strftime("%H:%M:%S")),
            ("ELAPSED", f"{int(elapsed)}s"),
            ("FPS", f"{int(self.clock.get_fps())}"),
            ("FRAMES", str(self.frame_count)),
            ("MODE", self.visualizer.mode.upper()),
            ("CRT", "ON" if self.crt_effects_enabled else "OFF"),
        ])

    def _render(self):
        """화면 렌더링"""
        # 버퍼 초기화
        self.buffer.fill(self.scheme.background)

        # 헤더
        self._draw_header()

        # 패널들
        self.viz_panel.draw(self.buffer, self.font)
        self.visualizer.draw(self.buffer)

        self.spectrum_panel.draw(self.buffer, self.font)
        self.spectrum_viz.draw(self.buffer)

        self.status_panel.draw(self.buffer, self.font)
        self._draw_system_status()

        self.file_panel.draw(self.buffer, self.font)
        self._draw_file_info()

        self.terminal_panel.draw(self.buffer, self.font)
        self._draw_terminal()

        # 상태 바
        self.status_bar.draw(self.buffer, self.font_small)

        # 도움말
        self._draw_help()

        # CRT 효과 적용
        if self.crt_effects_enabled and self.crt:
            final = self.crt.apply(self.buffer)
        else:
            final = self.buffer

        self.screen.blit(final, (0, 0))
        pygame.display.flip()

    def _draw_header(self):
        """헤더 그리기"""
        pygame.draw.rect(self.buffer, self.scheme.dim, self.header_rect)
        pygame.draw.line(
            self.buffer, self.scheme.border,
            (0, 40), (self.width, 40), 2
        )

        # 타이틀
        title = "████ MAINFRAME AUDIO VISUALIZATION SYSTEM v1.0 ████"
        title_surface = self.font_large.render(title, self.scheme.bright)
        title_x = (self.width - title_surface.get_width()) // 2
        self.buffer.blit(title_surface, (title_x, 10))

        # 장식 (좌우 인디케이터)
        for i in range(3):
            x_left = 20 + i * 15
            x_right = self.width - 40 - i * 15
            color = self.scheme.bright if (self.frame_count // 10) % 3 == i else self.scheme.dim
            pygame.draw.rect(self.buffer, color, (x_left, 15, 10, 10))
            pygame.draw.rect(self.buffer, color, (x_right, 15, 10, 10))

    def _draw_system_status(self):
        """시스템 상태 그리기"""
        rect = self.status_panel.content_rect
        y = rect.y + 5

        statuses = [
            ("SYSTEM", "ONLINE", self.scheme.bright),
            ("AUDIO ENGINE", "READY", self.scheme.bright),
            ("VISUALIZATION", "ACTIVE", self.scheme.bright),
            ("CRT EMULATION", "ON" if self.crt_effects_enabled else "OFF",
             self.scheme.bright if self.crt_effects_enabled else self.scheme.dim),
            ("PHOSPHOR TYPE", self.phosphor.value.upper(), self.scheme.foreground),
            ("MEMORY", "OK", self.scheme.bright),
        ]

        for label, value, color in statuses:
            # 라벨
            label_text = self.font_small.render(f"{label}:", self.scheme.foreground)
            self.buffer.blit(label_text, (rect.x + 5, y))

            # 값
            value_text = self.font_small.render(value, color)
            self.buffer.blit(value_text, (rect.x + 150, y))

            # 상태 인디케이터
            indicator_color = self.scheme.bright if value in ["ONLINE", "READY", "ACTIVE", "ON", "OK"] else self.scheme.dim
            pygame.draw.circle(self.buffer, indicator_color, (rect.x + 270, y + 6), 4)

            y += 18

    def _draw_file_info(self):
        """파일 정보 그리기"""
        rect = self.file_panel.content_rect
        y = rect.y + 5

        info = [
            ("FILE", self.current_file),
            ("FORMAT", "N/A"),
            ("DURATION", "00:00:00"),
            ("SAMPLE RATE", "44100 Hz"),
            ("CHANNELS", "2 (STEREO)"),
        ]

        for label, value in info:
            label_text = self.font_small.render(f"{label}:", self.scheme.dim)
            self.buffer.blit(label_text, (rect.x + 5, y))

            value_text = self.font_small.render(value, self.scheme.foreground)
            self.buffer.blit(value_text, (rect.x + 5, y + 12))

            y += 26

    def _draw_terminal(self):
        """터미널 로그 그리기"""
        rect = self.terminal_panel.content_rect
        y = rect.y + 5

        for line, color in self.terminal_lines[-15:]:
            text = self.font_small.render(line[:45], color)
            self.buffer.blit(text, (rect.x + 5, y))
            y += 14

        # 깜빡이는 커서
        if (self.frame_count // 15) % 2 == 0:
            cursor = self.font_small.render("█", self.scheme.bright)
            self.buffer.blit(cursor, (rect.x + 5, y))

    def _draw_help(self):
        """도움말 그리기"""
        help_text = "F1:WAVE  F2:SCOPE  F3:CRT  F4:COLOR  ESC:EXIT"
        text = self.font_small.render(help_text, self.scheme.dim)
        self.buffer.blit(text, (10, self.height - 45))


def run_app(
    phosphor: str = "green",
    width: int = 1024,
    height: int = 768,
    crt_effects: bool = True,
):
    """
    메인프레임 GUI 애플리케이션 실행

    Args:
        phosphor: 인광체 색상 ("green", "amber", "white", "blue")
        width: 창 너비
        height: 창 높이
        crt_effects: CRT 효과 활성화 여부
    """
    phosphor_color = PhosphorColor(phosphor.lower())
    app = MainframeApp(
        width=width,
        height=height,
        phosphor=phosphor_color,
        crt_effects=crt_effects,
    )
    app.run()


if __name__ == "__main__":
    run_app()
