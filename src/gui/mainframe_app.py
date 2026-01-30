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
from typing import Optional, Tuple, List
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

# 시각화 및 오디오 모듈 임포트
from .visualizations import (
    VISUALIZATIONS, create_visualization, get_visualization_list,
    BaseVisualization, VisualizationCategory
)
from .audio_input import (
    AudioInputManager, AudioInputType, AudioDevice, AudioState
)


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

    def __init__(self, size: int = 16, font_path: Optional[str] = None):
        pygame.font.init()

        self.font = None

        # 커스텀 폰트 시도
        if font_path:
            try:
                self.font = pygame.font.Font(font_path, size)
            except Exception:
                pass

        # 폴백: 프로젝트 루트의 NeoDunggeunmoPro-Regular.ttf
        if self.font is None:
            try:
                project_root = Path(__file__).parent.parent.parent
                neo_font = project_root / "NeoDunggeunmoPro-Regular.ttf"
                if neo_font.exists():
                    self.font = pygame.font.Font(str(neo_font), size)
            except Exception:
                pass

        # 폴백: 시스템 모노스페이스 폰트
        if self.font is None:
            font_names = [
                "Consolas", "Courier New", "Lucida Console",
                "Monaco", "DejaVu Sans Mono", "monospace"
            ]
            for name in font_names:
                try:
                    self.font = pygame.font.SysFont(name, size)
                    break
                except Exception:
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


class SettingsScreen:
    """설정 화면"""

    def __init__(self, width: int, height: int, scheme: ColorScheme,
                 audio_manager: AudioInputManager, font: TerminalFont):
        self.width = width
        self.height = height
        self.scheme = scheme
        self.audio_manager = audio_manager
        self.font = font
        self.visible = False
        self.selected_index = 0
        self.menu_items: List[Tuple[str, str]] = []
        self.devices: List[AudioDevice] = []

        self._refresh_menu()

    def _refresh_menu(self):
        """메뉴 항목 새로고침"""
        self.devices = self.audio_manager.get_input_devices()
        self.menu_items = [
            ("demo", "DEMO MODE"),
            ("file", "OPEN FILE..."),
        ]

        for dev in self.devices:
            prefix = "[LOOPBACK] " if dev.is_loopback else "[MIC] "
            self.menu_items.append((f"device_{dev.index}", f"{prefix}{dev.name[:40]}"))

        self.menu_items.append(("close", "CLOSE SETTINGS"))

    def show(self):
        """설정 화면 표시"""
        self._refresh_menu()
        self.visible = True
        self.selected_index = 0

    def hide(self):
        """설정 화면 숨기기"""
        self.visible = False

    def handle_event(self, event) -> Optional[str]:
        """이벤트 처리, 선택된 항목 ID 반환"""
        if not self.visible:
            return None

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                self.hide()
                return None
            elif event.key == K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.menu_items)
            elif event.key == K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.menu_items)
            elif event.key == K_RETURN:
                item_id, _ = self.menu_items[self.selected_index]
                return item_id

        return None

    def draw(self, surface: Surface):
        """설정 화면 그리기"""
        if not self.visible:
            return

        # 반투명 배경
        overlay = Surface((self.width, self.height), SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        # 설정 창
        panel_width = 500
        panel_height = min(400, 100 + len(self.menu_items) * 25)
        panel_x = (self.width - panel_width) // 2
        panel_y = (self.height - panel_height) // 2

        panel_rect = Rect(panel_x, panel_y, panel_width, panel_height)

        # 배경
        pygame.draw.rect(surface, self.scheme.background, panel_rect)
        pygame.draw.rect(surface, self.scheme.border, panel_rect, 3)

        # 타이틀
        title = "■ AUDIO INPUT SETTINGS ■"
        title_surface = self.font.render(title, self.scheme.bright)
        surface.blit(title_surface, (panel_x + 20, panel_y + 15))

        pygame.draw.line(
            surface, self.scheme.border,
            (panel_x + 10, panel_y + 40),
            (panel_x + panel_width - 10, panel_y + 40)
        )

        # 메뉴 항목
        y = panel_y + 55
        for i, (item_id, item_name) in enumerate(self.menu_items):
            is_selected = i == self.selected_index

            if is_selected:
                # 선택 하이라이트
                pygame.draw.rect(
                    surface, self.scheme.dim,
                    (panel_x + 10, y - 2, panel_width - 20, 22)
                )
                prefix = "> "
                color = self.scheme.bright
            else:
                prefix = "  "
                color = self.scheme.foreground

            text = f"{prefix}{item_name}"
            text_surface = self.font.render(text, color)
            surface.blit(text_surface, (panel_x + 20, y))

            y += 25

        # 도움말
        help_text = "UP/DOWN: Select  ENTER: Confirm  ESC: Close"
        help_surface = self.font.render(help_text, self.scheme.dim)
        surface.blit(help_surface, (panel_x + 20, panel_y + panel_height - 30))


class VisualizationSelector:
    """시각화 선택기"""

    def __init__(self, scheme: ColorScheme):
        self.scheme = scheme
        self.viz_list = list(VISUALIZATIONS.keys())
        self.current_index = 0
        self.categories = list(VisualizationCategory)
        self.current_category_index = 0
        self.filter_by_category = False

    def next(self):
        """다음 시각화"""
        self.current_index = (self.current_index + 1) % len(self.viz_list)

    def prev(self):
        """이전 시각화"""
        self.current_index = (self.current_index - 1) % len(self.viz_list)

    def next_category(self):
        """다음 카테고리"""
        self.current_category_index = (self.current_category_index + 1) % len(self.categories)

    def get_current_id(self) -> str:
        """현재 시각화 ID"""
        return self.viz_list[self.current_index]

    def get_current_info(self) -> Tuple[str, str, str]:
        """현재 시각화 정보 (id, name, name_kr)"""
        viz_id = self.viz_list[self.current_index]
        _, info = VISUALIZATIONS[viz_id]
        return viz_id, info.name, info.name_kr

    def get_index_text(self) -> str:
        """인덱스 텍스트"""
        return f"{self.current_index + 1}/{len(self.viz_list)}"


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

        # 폰트 (NeoDunggeunmoPro 사용)
        self.font = TerminalFont(14)
        self.font_large = TerminalFont(18)
        self.font_small = TerminalFont(12)

        # 오디오 관리자
        self.audio_manager = AudioInputManager()

        # 시각화 선택기
        self.viz_selector = VisualizationSelector(self.scheme)

        # 현재 시각화
        self._current_visualization: Optional[BaseVisualization] = None
        self._secondary_visualization: Optional[BaseVisualization] = None
        self._setup_visualization()

        # UI 컴포넌트
        self._setup_ui()

        # 설정 화면
        self.settings_screen = SettingsScreen(
            width, height, self.scheme, self.audio_manager, self.font
        )

        # 상태
        self.frame_count = 0
        self.start_time = time.time()
        self.current_file = "NO FILE LOADED"
        self.system_status = "STANDBY"

        # 터미널 로그
        self.terminal_lines: List[Tuple[str, Tuple[int, int, int]]] = []
        self.max_terminal_lines = 20

        # 데모 모드 자동 시작
        self.audio_manager.start_demo()

    def _get_colors_dict(self) -> dict:
        """색상 스킴을 dict로 변환"""
        return {
            'background': self.scheme.background,
            'foreground': self.scheme.foreground,
            'dim': self.scheme.dim,
            'bright': self.scheme.bright,
            'highlight': self.scheme.highlight,
            'warning': self.scheme.warning,
            'error': self.scheme.error,
            'border': self.scheme.border,
        }

    def _setup_visualization(self):
        """시각화 설정"""
        viz_id = self.viz_selector.get_current_id()
        colors = self._get_colors_dict()

        # 메인 시각화 영역
        viz_width = self.width - 320
        viz_rect = Rect(14, 72, viz_width - 28, 370)
        self._current_visualization = create_visualization(viz_id, viz_rect, colors)

        # 하단 스펙트럼 영역 (항상 spectrum_bars)
        spectrum_rect = Rect(14, 482, viz_width - 28, 170)
        self._secondary_visualization = create_visualization("spectrum_bars", spectrum_rect, colors)

    def _setup_ui(self):
        """UI 컴포넌트 설정"""
        # 헤더
        self.header_rect = Rect(0, 0, self.width, 40)

        # 메인 시각화 패널
        viz_width = self.width - 320
        viz_id, viz_name, viz_name_kr = self.viz_selector.get_current_info()
        self.viz_panel = Panel(
            Rect(10, 50, viz_width - 20, 400),
            f"■ {viz_name_kr.upper()} ({self.viz_selector.get_index_text()}) ■",
            self.scheme
        )

        # 스펙트럼 패널
        self.spectrum_panel = Panel(
            Rect(10, 460, viz_width - 20, 200),
            "■ FREQUENCY SPECTRUM ■",
            self.scheme
        )

        # 사이드 패널 - 시스템 상태
        side_x = self.width - 300
        self.status_panel = Panel(
            Rect(side_x, 50, 290, 200),
            "■ SYSTEM STATUS ■",
            self.scheme
        )

        # 사이드 패널 - 파일/오디오 정보
        self.file_panel = Panel(
            Rect(side_x, 260, 290, 150),
            "■ AUDIO INFO ■",
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

    def _update_panel_title(self):
        """시각화 패널 타이틀 업데이트"""
        viz_id, viz_name, viz_name_kr = self.viz_selector.get_current_info()
        viz_width = self.width - 320
        self.viz_panel = Panel(
            Rect(10, 50, viz_width - 20, 400),
            f"■ {viz_name_kr.upper()} ({self.viz_selector.get_index_text()}) ■",
            self.scheme
        )

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

    def _open_file_dialog(self) -> Optional[str]:
        """파일 열기 다이얼로그 (tkinter 사용)"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            formats = self.audio_manager.get_supported_formats()
            filetypes = [
                ("Audio Files", " ".join(f"*{fmt}" for fmt in formats)),
                ("All Files", "*.*"),
            ]

            file_path = filedialog.askopenfilename(
                title="Select Audio File",
                filetypes=filetypes
            )
            root.destroy()

            return file_path if file_path else None
        except Exception as e:
            self.log(f"FILE DIALOG ERROR: {e}", "ERROR")
            return None

    def run(self):
        """메인 루프 실행"""
        self.running = True
        self.start_time = time.time()

        self.log("SYSTEM INITIALIZATION COMPLETE", "OK")
        self.log("AUDIO SUBSYSTEM ONLINE", "OK")
        self.log("52 VISUALIZATION MODES LOADED", "OK")
        self.log("PRESS F5 FOR SETTINGS", "INFO")

        while self.running:
            self._handle_events()
            self._update()
            self._render()
            self.clock.tick(self.fps)

        self.audio_manager.stop()
        pygame.quit()

    def _handle_events(self):
        """이벤트 처리"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False

            # 설정 화면이 열려있으면 설정 화면에서 처리
            if self.settings_screen.visible:
                result = self.settings_screen.handle_event(event)
                if result:
                    self._handle_settings_selection(result)
                continue

            if event.type == KEYDOWN:
                self._handle_keydown(event)

    def _handle_keydown(self, event):
        """키 입력 처리"""
        if event.key == K_ESCAPE:
            self.running = False

        elif event.key == K_F1:
            # 이전 시각화
            self.viz_selector.prev()
            self._switch_visualization()

        elif event.key == K_F2:
            # 다음 시각화
            self.viz_selector.next()
            self._switch_visualization()

        elif event.key == K_F3:
            # CRT 효과 토글
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
            self._setup_visualization()
            self.log(f"PHOSPHOR: {self.phosphor.value.upper()}", "INFO")

        elif event.key == K_F5:
            # 설정 화면 열기
            self.settings_screen.show()
            self.log("SETTINGS OPENED", "INFO")

        elif event.key == K_SPACE:
            # 일시정지/재개
            state = self.audio_manager.get_state()
            if state.input_type == AudioInputType.FILE:
                if state.is_playing:
                    self.audio_manager.pause()
                    self.log("PLAYBACK PAUSED", "INFO")
                else:
                    self.audio_manager.resume()
                    self.log("PLAYBACK RESUMED", "INFO")

        elif event.key == K_LEFT:
            # 시각화 이전
            self.viz_selector.prev()
            self._switch_visualization()

        elif event.key == K_RIGHT:
            # 시각화 다음
            self.viz_selector.next()
            self._switch_visualization()

    def _handle_settings_selection(self, selection: str):
        """설정 선택 처리"""
        if selection == "close":
            self.settings_screen.hide()

        elif selection == "demo":
            self.audio_manager.start_demo()
            self.current_file = "DEMO MODE"
            self.log("DEMO MODE ACTIVATED", "OK")
            self.settings_screen.hide()

        elif selection == "file":
            file_path = self._open_file_dialog()
            if file_path:
                if self.audio_manager.load_file(file_path):
                    self.current_file = Path(file_path).name
                    self.log(f"LOADED: {self.current_file}", "OK")
                else:
                    self.log("FILE LOAD FAILED", "ERROR")
            self.settings_screen.hide()

        elif selection.startswith("device_"):
            try:
                device_index = int(selection.split("_")[1])
                if self.audio_manager.start_device(device_index):
                    state = self.audio_manager.get_state()
                    self.current_file = state.device_name[:30]
                    input_type = "LOOPBACK" if state.input_type == AudioInputType.LOOPBACK else "MIC"
                    self.log(f"{input_type} INPUT ACTIVE", "OK")
                else:
                    self.log("DEVICE INIT FAILED", "ERROR")
            except (ValueError, IndexError):
                self.log("INVALID DEVICE", "ERROR")
            self.settings_screen.hide()

    def _switch_visualization(self):
        """시각화 전환"""
        viz_id, viz_name, viz_name_kr = self.viz_selector.get_current_info()
        colors = self._get_colors_dict()

        viz_width = self.width - 320
        viz_rect = Rect(14, 72, viz_width - 28, 370)
        self._current_visualization = create_visualization(viz_id, viz_rect, colors)
        self._update_panel_title()
        self.log(f"VIZ: {viz_name_kr.upper()}", "INFO")

    def _update(self):
        """상태 업데이트"""
        self.frame_count += 1
        dt = 1.0 / self.fps

        # 시각화 업데이트
        if self._current_visualization:
            self._current_visualization.update(dt)
        if self._secondary_visualization:
            self._secondary_visualization.update(dt)

        # 오디오 상태
        state = self.audio_manager.get_state()

        # 상태 바 업데이트
        elapsed = time.time() - self.start_time
        viz_id, viz_name, viz_name_kr = self.viz_selector.get_current_info()

        self.status_bar.set_items([
            ("TIME", time.strftime("%H:%M:%S")),
            ("FPS", f"{int(self.clock.get_fps())}"),
            ("VIZ", f"{self.viz_selector.get_index_text()}"),
            ("INPUT", state.input_type.value.upper()[:6]),
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

        # 메인 시각화 렌더링
        waveform = self.audio_manager.get_waveform()
        spectrum = self.audio_manager.get_spectrum()

        if self._current_visualization:
            self._current_visualization.render(
                self.buffer, waveform, spectrum, font=self.font_small
            )

        # 스펙트럼 패널
        self.spectrum_panel.draw(self.buffer, self.font)
        if self._secondary_visualization:
            self._secondary_visualization.render(
                self.buffer, waveform, spectrum, font=self.font_small
            )

        # 사이드 패널들
        self.status_panel.draw(self.buffer, self.font)
        self._draw_system_status()

        self.file_panel.draw(self.buffer, self.font)
        self._draw_audio_info()

        self.terminal_panel.draw(self.buffer, self.font)
        self._draw_terminal()

        # 상태 바
        self.status_bar.draw(self.buffer, self.font_small)

        # 도움말
        self._draw_help()

        # 설정 화면
        self.settings_screen.draw(self.buffer)

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
        title = "████ MAINFRAME AUDIO VISUALIZATION SYSTEM v2.0 ████"
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

        audio_state = self.audio_manager.get_state()

        statuses = [
            ("SYSTEM", "ONLINE", self.scheme.bright),
            ("AUDIO ENGINE", "READY", self.scheme.bright),
            ("INPUT TYPE", audio_state.input_type.value.upper(), self.scheme.foreground),
            ("VISUALIZATION", "ACTIVE", self.scheme.bright),
            ("CRT EMULATION", "ON" if self.crt_effects_enabled else "OFF",
             self.scheme.bright if self.crt_effects_enabled else self.scheme.dim),
            ("PHOSPHOR TYPE", self.phosphor.value.upper(), self.scheme.foreground),
        ]

        for label, value, color in statuses:
            # 라벨
            label_text = self.font_small.render(f"{label}:", self.scheme.foreground)
            self.buffer.blit(label_text, (rect.x + 5, y))

            # 값
            value_text = self.font_small.render(value, color)
            self.buffer.blit(value_text, (rect.x + 140, y))

            # 상태 인디케이터
            indicator_color = self.scheme.bright if value in ["ONLINE", "READY", "ACTIVE", "ON"] else self.scheme.dim
            pygame.draw.circle(self.buffer, indicator_color, (rect.x + 265, y + 6), 4)

            y += 18

    def _draw_audio_info(self):
        """오디오 정보 그리기"""
        rect = self.file_panel.content_rect
        y = rect.y + 5

        state = self.audio_manager.get_state()

        # 재생 상태
        if state.input_type == AudioInputType.FILE:
            status = "PLAYING" if state.is_playing else "PAUSED"
        elif state.input_type == AudioInputType.DEMO:
            status = "GENERATING"
        elif state.input_type in [AudioInputType.MICROPHONE, AudioInputType.LOOPBACK]:
            status = "CAPTURING"
        else:
            status = "STOPPED"

        info = [
            ("SOURCE", self.current_file[:25] if self.current_file else "N/A"),
            ("STATUS", status),
            ("SAMPLE RATE", f"{state.sample_rate} Hz"),
            ("CHANNELS", str(state.channels)),
        ]

        if state.input_type == AudioInputType.FILE and state.duration > 0:
            position_sec = state.position * state.duration
            duration_str = f"{int(position_sec)}/{int(state.duration)}s"
            info.append(("POSITION", duration_str))

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
            text = self.font_small.render(line[:42], color)
            self.buffer.blit(text, (rect.x + 5, y))
            y += 14

        # 깜빡이는 커서
        if (self.frame_count // 15) % 2 == 0:
            cursor = self.font_small.render("█", self.scheme.bright)
            self.buffer.blit(cursor, (rect.x + 5, y))

    def _draw_help(self):
        """도움말 그리기"""
        help_text = "F1/F2:VIZ  F3:CRT  F4:COLOR  F5:SETTINGS  SPACE:PAUSE  ESC:EXIT"
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
