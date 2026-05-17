"""
매트릭스 레인 시각화

오디오 반응형 매트릭스 스타일 레인 효과
"""

import numpy as np
from matplotlib.font_manager import FontProperties

from src.analysis.result import AnalysisResult
from src.utils.logging import get_logger
from src.visualization.artistic.base_artistic import BaseArtisticVisualizer

logger = get_logger(__name__)


class MatrixRainVisualizer(BaseArtisticVisualizer):
    """
    매트릭스 레인 시각화

    영화 매트릭스 스타일의 떨어지는 문자 효과
    """

    # 매트릭스 스타일 문자 (일본어 카타카나 + 숫자 + 기호)
    MATRIX_CHARS = (
        "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"
        "0123456789"
        "!@#$%^&*()+-=[]{}|;:,.<>?"
    )

    def __init__(self, config_override: dict = None):
        """
        MatrixRainVisualizer 초기화

        Args:
            config_override: 설정 오버라이드
        """
        super().__init__(config_override)
        self.columns = []
        self.initialized = False

    def _init_columns(self, num_cols: int, num_rows: int):
        """
        레인 컬럼 초기화

        Args:
            num_cols: 열 수
            num_rows: 행 수
        """
        self.columns = []

        for i in range(num_cols):
            column = {
                'chars': [self._random_char() for _ in range(num_rows)],
                'y': np.random.randint(-num_rows, 0),
                'speed': np.random.uniform(0.5, 2.0),
                'length': np.random.randint(5, 20),
                'brightness': np.random.uniform(0.5, 1.0),
            }
            self.columns.append(column)

        self.initialized = True

    def _random_char(self) -> str:
        """랜덤 매트릭스 문자 반환"""
        return np.random.choice(list(self.MATRIX_CHARS))

    def render(
        self,
        result: AnalysisResult,
        cols: int = 60,
        rows: int = 40,
        time: float = 0.0,
        rain_speed: float = 1.0,
        **kwargs
    ):
        """
        매트릭스 레인 시각화 렌더링

        Args:
            result: 분석 결과
            cols: 열 수
            rows: 행 수
            time: 애니메이션 시간
            rain_speed: 레인 속도
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        self.create_figure()

        # 컬럼 초기화
        if not self.initialized or len(self.columns) != cols:
            self._init_columns(cols, rows)

        # 오디오 반응형 파라미터
        energy = self.get_audio_reactive_value(result, "energy")
        centroid = self.get_audio_reactive_value(result, "centroid")
        brightness = self.get_audio_reactive_value(result, "brightness")

        # 컬럼 업데이트
        self._update_columns(rows, rain_speed * (0.5 + energy), time)

        # 렌더링
        self._render_rain(cols, rows, energy, centroid, brightness)

        # 축 설정
        self.ax.set_xlim(0, cols)
        self.ax.set_ylim(0, rows)
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        # 제목
        tempo = result.rhythm.get("tempo", 120)
        self.set_title(f"Matrix Rain - {tempo:.0f} BPM")

        logger.info(f"매트릭스 레인 시각화 완료: {cols}x{rows}")
        return self.fig

    def _update_columns(self, num_rows: int, speed: float, time: float):
        """
        컬럼 상태 업데이트

        Args:
            num_rows: 행 수
            speed: 속도
            time: 시간
        """
        for col in self.columns:
            # 위치 업데이트
            col['y'] += col['speed'] * speed

            # 화면 밖으로 나가면 리셋
            if col['y'] - col['length'] > num_rows:
                col['y'] = np.random.randint(-20, -5)
                col['length'] = np.random.randint(5, 20)
                col['speed'] = np.random.uniform(0.5, 2.0)
                col['brightness'] = np.random.uniform(0.5, 1.0)

            # 랜덤하게 문자 변경 (글리치 효과)
            if np.random.random() < 0.1:
                change_idx = np.random.randint(0, len(col['chars']))
                col['chars'][change_idx] = self._random_char()

    def _render_rain(
        self,
        cols: int,
        rows: int,
        energy: float,
        centroid: float,
        brightness_factor: float
    ):
        """
        레인 렌더링

        Args:
            cols: 열 수
            rows: 행 수
            energy: 에너지 값
            centroid: centroid 값
            brightness_factor: 밝기 인자
        """
        try:
            font = FontProperties(family='monospace', size=8)
        except:
            font = FontProperties(size=8)

        for col_idx, column in enumerate(self.columns):
            head_y = int(column['y'])

            for i in range(column['length']):
                char_y = head_y - i
                if 0 <= char_y < rows:
                    # 문자 인덱스
                    char_idx = (head_y - i) % len(column['chars'])
                    char = column['chars'][char_idx]

                    # 밝기 계산 (헤드가 가장 밝음)
                    if i == 0:
                        # 헤드 (흰색)
                        alpha = 1.0
                        color = (1.0, 1.0, 1.0)
                    else:
                        # 테일 (점점 어두워짐)
                        fade = 1.0 - (i / column['length'])
                        alpha = fade * column['brightness'] * (0.7 + energy * 0.3)

                        # 녹색 계열
                        green_intensity = 0.4 + fade * 0.6
                        color = (0, green_intensity * (0.8 + brightness_factor * 0.2), 0)

                    # 문자 그리기
                    self.ax.text(
                        col_idx + 0.5,
                        rows - char_y - 0.5,
                        char,
                        fontproperties=font,
                        ha='center',
                        va='center',
                        color=color,
                        alpha=min(1.0, alpha)
                    )

    def render_to_array(
        self,
        result: AnalysisResult,
        cols: int = 60,
        rows: int = 40,
        time: float = 0.0
    ) -> np.ndarray:
        """
        매트릭스 레인을 배열로 렌더링

        Args:
            result: 분석 결과
            cols: 열 수
            rows: 행 수
            time: 시간

        Returns:
            (rows, cols) 형태의 밝기 배열
        """
        if not self.initialized or len(self.columns) != cols:
            self._init_columns(cols, rows)

        energy = self.get_audio_reactive_value(result, "energy")

        # 배열 초기화
        rain_array = np.zeros((rows, cols))

        for col_idx, column in enumerate(self.columns):
            head_y = int(column['y'])

            for i in range(column['length']):
                char_y = head_y - i
                if 0 <= char_y < rows:
                    if i == 0:
                        brightness = 1.0
                    else:
                        fade = 1.0 - (i / column['length'])
                        brightness = fade * column['brightness'] * (0.7 + energy * 0.3)

                    rain_array[rows - char_y - 1, col_idx] = brightness

        return rain_array

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
        time = (frame_index / total_frames) * 10  # 시간 스케일

        return self.render(
            result,
            time=time,
            **kwargs
        )

    def reset(self):
        """상태 초기화"""
        self.columns = []
        self.initialized = False
