"""
ASCII 아트 렌더러

오디오 시각화를 ASCII 아트로 변환
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from src.analysis.result import AnalysisResult
from src.visualization.artistic.base_artistic import BaseArtisticVisualizer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ASCIIRenderer(BaseArtisticVisualizer):
    """
    ASCII 아트 렌더러

    이미지나 시각화를 ASCII 문자로 변환
    """

    # 밝기에 따른 문자 (어두운 것부터 밝은 것)
    ASCII_CHARS_SIMPLE = " .:-=+*#%@"
    ASCII_CHARS_DETAILED = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
    ASCII_BLOCKS = " ░▒▓█"

    def __init__(self, config_override: dict = None):
        """
        ASCIIRenderer 초기화

        Args:
            config_override: 설정 오버라이드
        """
        super().__init__(config_override)
        self.char_set = self.ASCII_CHARS_DETAILED

    def render(
        self,
        result: AnalysisResult,
        mode: str = "waveform",
        cols: int = 80,
        rows: int = 40,
        char_set: str = "detailed",
        colored: bool = True,
        time: float = 0.0,
        **kwargs
    ):
        """
        ASCII 아트 시각화 렌더링

        Args:
            result: 분석 결과
            mode: 렌더링 모드 ("waveform", "spectrum", "pattern", "image")
            cols: 열 수
            rows: 행 수
            char_set: 문자 세트 ("simple", "detailed", "blocks")
            colored: 색상 사용 여부
            time: 애니메이션 시간
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        self.create_figure()

        # 문자 세트 선택
        if char_set == "simple":
            self.char_set = self.ASCII_CHARS_SIMPLE
        elif char_set == "blocks":
            self.char_set = self.ASCII_BLOCKS
        else:
            self.char_set = self.ASCII_CHARS_DETAILED

        # 오디오 반응형 파라미터
        energy = self.get_audio_reactive_value(result, "energy")
        centroid = self.get_audio_reactive_value(result, "centroid")

        # 모드에 따른 렌더링
        if mode == "waveform":
            ascii_art, colors = self._render_waveform(result, cols, rows, time, energy)
        elif mode == "spectrum":
            ascii_art, colors = self._render_spectrum(result, cols, rows, energy, centroid)
        elif mode == "pattern":
            ascii_art, colors = self._render_pattern(cols, rows, time, energy, centroid)
        else:
            ascii_art, colors = self._render_pattern(cols, rows, time, energy, centroid)

        # 텍스트로 표시
        self._display_ascii(ascii_art, colors if colored else None)

        # 제목
        tempo = result.rhythm.get("tempo", 120)
        self.set_title(f"ASCII Art ({mode}) - {tempo:.0f} BPM")

        logger.info(f"ASCII 렌더링 완료: {cols}x{rows}, 모드: {mode}")
        return self.fig

    def _render_waveform(
        self,
        result: AnalysisResult,
        cols: int,
        rows: int,
        time: float,
        energy: float
    ) -> tuple:
        """
        파형 ASCII 렌더링

        Args:
            result: 분석 결과
            cols: 열 수
            rows: 행 수
            time: 시간
            energy: 에너지 값

        Returns:
            (ASCII 문자열 리스트, 색상 리스트)
        """
        ascii_art = []
        colors = []
        center_row = rows // 2

        # RMS 에너지 가져오기
        rms = result.timbre.get("rms_energy")
        if rms is not None and len(rms) > 0:
            rms_interp = self.interpolate_feature(rms, cols)
            rms_norm = self.normalize_feature(rms_interp)
        else:
            # 시뮬레이션
            rms_norm = np.array([
                0.5 + 0.4 * np.sin(i / cols * np.pi * 4 + time * 3)
                for i in range(cols)
            ])

        for row in range(rows):
            line = ""
            line_colors = []

            for col in range(cols):
                # 파형 높이 계산
                amplitude = rms_norm[col] * (rows // 2 - 1) * (0.5 + energy * 0.5)
                wave_top = center_row - int(amplitude)
                wave_bottom = center_row + int(amplitude)

                if wave_top <= row <= wave_bottom:
                    # 파형 내부
                    intensity = 1.0 - abs(row - center_row) / (amplitude + 1)
                    char_idx = int(intensity * (len(self.char_set) - 1))
                    line += self.char_set[char_idx]
                    line_colors.append((0, 1, intensity))  # 시안 계열
                else:
                    line += " "
                    line_colors.append((0.1, 0.1, 0.1))

            ascii_art.append(line)
            colors.append(line_colors)

        return ascii_art, colors

    def _render_spectrum(
        self,
        result: AnalysisResult,
        cols: int,
        rows: int,
        energy: float,
        centroid: float
    ) -> tuple:
        """
        스펙트럼 ASCII 렌더링

        Args:
            result: 분석 결과
            cols: 열 수
            rows: 행 수
            energy: 에너지 값
            centroid: centroid 값

        Returns:
            (ASCII 문자열 리스트, 색상 리스트)
        """
        ascii_art = []
        colors = []

        # 스펙트럼 데이터
        spectrum = result.spectral.get("spectrum")
        if spectrum is not None and len(spectrum) > 0:
            spec_interp = self.interpolate_feature(spectrum[:len(spectrum)//2], cols)
            spec_norm = self.normalize_feature(spec_interp)
        else:
            # 시뮬레이션
            spec_norm = np.array([
                np.exp(-i / cols * 3) * (0.5 + energy * 0.5)
                for i in range(cols)
            ])

        for row in range(rows):
            line = ""
            line_colors = []
            threshold = 1.0 - (row / rows)

            for col in range(cols):
                magnitude = spec_norm[col]

                if magnitude >= threshold:
                    # 스펙트럼 바 내부
                    char_idx = int(magnitude * (len(self.char_set) - 1))
                    line += self.char_set[min(char_idx, len(self.char_set) - 1)]

                    # 주파수에 따른 색상 (저주파=빨강, 고주파=파랑)
                    hue = col / cols
                    line_colors.append(self._hue_to_rgb(hue))
                else:
                    line += " "
                    line_colors.append((0.05, 0.05, 0.05))

            ascii_art.append(line)
            colors.append(line_colors)

        return ascii_art, colors

    def _render_pattern(
        self,
        cols: int,
        rows: int,
        time: float,
        energy: float,
        centroid: float
    ) -> tuple:
        """
        패턴 ASCII 렌더링

        Args:
            cols: 열 수
            rows: 행 수
            time: 시간
            energy: 에너지 값
            centroid: centroid 값

        Returns:
            (ASCII 문자열 리스트, 색상 리스트)
        """
        ascii_art = []
        colors = []

        center_x = cols / 2
        center_y = rows / 2

        for row in range(rows):
            line = ""
            line_colors = []

            for col in range(cols):
                # 중심으로부터의 거리
                dx = (col - center_x) / cols * 2
                dy = (row - center_y) / rows * 2
                dist = np.sqrt(dx**2 + dy**2)
                angle = np.arctan2(dy, dx)

                # 패턴 계산
                pattern = np.sin(dist * 10 - time * 3) * np.cos(angle * 3 + time)
                pattern += np.sin(angle * 5 + dist * 5 + time * 2) * 0.5

                # 에너지 반응
                pattern *= (0.5 + energy * 0.5)

                # 정규화
                value = (pattern + 1.5) / 3
                value = np.clip(value, 0, 1)

                # 문자 선택
                char_idx = int(value * (len(self.char_set) - 1))
                line += self.char_set[char_idx]

                # 색상 (centroid 기반 색조)
                hue = (value + centroid) % 1.0
                line_colors.append(self._hue_to_rgb(hue))

            ascii_art.append(line)
            colors.append(line_colors)

        return ascii_art, colors

    def _display_ascii(self, ascii_art: list, colors: list = None):
        """
        ASCII 아트를 Figure에 표시

        Args:
            ascii_art: ASCII 문자열 리스트
            colors: 색상 리스트 (옵션)
        """
        rows = len(ascii_art)
        cols = len(ascii_art[0]) if ascii_art else 0

        # 축 설정
        self.ax.set_xlim(0, cols)
        self.ax.set_ylim(0, rows)
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        # 모노스페이스 폰트
        try:
            font = FontProperties(family='monospace', size=6)
        except:
            font = FontProperties(size=6)

        for row_idx, line in enumerate(ascii_art):
            y = rows - row_idx - 1  # 위에서 아래로

            if colors and colors[row_idx]:
                # 문자별 색상
                for col_idx, char in enumerate(line):
                    if char != ' ':
                        color = colors[row_idx][col_idx]
                        self.ax.text(
                            col_idx + 0.5, y + 0.5, char,
                            fontproperties=font,
                            ha='center', va='center',
                            color=color
                        )
            else:
                # 단색
                self.ax.text(
                    0, y + 0.5, line,
                    fontproperties=font,
                    ha='left', va='center',
                    color='lime'
                )

    def _hue_to_rgb(self, h: float) -> tuple:
        """
        HSV에서 RGB로 변환 (S=1, V=1)

        Args:
            h: 색조 (0-1)

        Returns:
            (R, G, B) 튜플
        """
        h = h % 1.0
        i = int(h * 6)
        f = h * 6 - i

        if i == 0:
            return (1, f, 0)
        elif i == 1:
            return (1 - f, 1, 0)
        elif i == 2:
            return (0, 1, f)
        elif i == 3:
            return (0, 1 - f, 1)
        elif i == 4:
            return (f, 0, 1)
        else:
            return (1, 0, 1 - f)

    def image_to_ascii(
        self,
        image: np.ndarray,
        cols: int = 80,
        invert: bool = False
    ) -> str:
        """
        이미지를 ASCII 문자열로 변환

        Args:
            image: 입력 이미지 (RGB 또는 그레이스케일)
            cols: 출력 열 수
            invert: 밝기 반전

        Returns:
            ASCII 문자열
        """
        # 그레이스케일 변환
        if len(image.shape) == 3:
            gray = np.mean(image, axis=2)
        else:
            gray = image

        # 크기 조정
        height, width = gray.shape
        aspect = height / width
        rows = int(cols * aspect * 0.5)  # 문자 높이 보정

        # 리샘플링
        row_indices = np.linspace(0, height - 1, rows).astype(int)
        col_indices = np.linspace(0, width - 1, cols).astype(int)

        ascii_lines = []

        for row_idx in row_indices:
            line = ""
            for col_idx in col_indices:
                brightness = gray[row_idx, col_idx] / 255

                if invert:
                    brightness = 1 - brightness

                char_idx = int(brightness * (len(self.char_set) - 1))
                line += self.char_set[char_idx]

            ascii_lines.append(line)

        return "\n".join(ascii_lines)

    def render_animation_frame(
        self,
        result: AnalysisResult,
        frame_index: int,
        total_frames: int,
        **kwargs
    ):
        """
        애니메이션 프레임 렌더링

        Args:
            result: 분석 결과
            frame_index: 현재 프레임 인덱스
            total_frames: 총 프레임 수
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        time = (frame_index / total_frames) * np.pi * 4

        return self.render(
            result,
            time=time,
            **kwargs
        )
