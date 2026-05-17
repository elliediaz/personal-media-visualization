"""
파형 시각화

오디오 파형을 시각화합니다.
"""

from pathlib import Path

import librosa
import numpy as np

from src.analysis.result import AnalysisResult
from src.utils.logging import get_logger
from src.visualization.base import BaseVisualizer

logger = get_logger(__name__)


class WaveformVisualizer(BaseVisualizer):
    """파형 시각화기"""

    def render(
        self,
        audio_data: np.ndarray = None,
        sr: int = None,
        file_path: Path | str = None,
        result: AnalysisResult = None,
        **kwargs
    ):
        """
        파형 렌더링

        Args:
            audio_data: 오디오 신호 (선택)
            sr: 샘플링 레이트 (선택)
            file_path: 오디오 파일 경로 (선택)
            result: 분석 결과 (선택)
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        # 오디오 데이터 로드
        if audio_data is None:
            if file_path is not None:
                audio_data, sr = librosa.load(str(file_path), sr=sr)
            elif result is not None and result.file_path is not None:
                audio_data, sr = librosa.load(str(result.file_path), sr=sr)
            else:
                raise ValueError("오디오 데이터 또는 파일 경로가 필요합니다")

        # Figure 생성
        self.create_figure()

        # 시간 축 생성
        times = librosa.times_like(audio_data, sr=sr)

        # 파형 그리기
        line_width = kwargs.get("line_width", 0.5)
        alpha = kwargs.get("alpha", 0.8)

        self.ax.plot(times, audio_data, color=self.primary_color, linewidth=line_width, alpha=alpha)
        self.ax.fill_between(times, audio_data, alpha=alpha * 0.3, color=self.primary_color)

        # 레이블 및 제목
        self.set_title("파형 (Waveform)")
        self.set_labels("시간 (초)", "진폭")
        self.add_grid()

        # y축 범위
        self.ax.set_ylim([-1.1, 1.1])

        logger.info("파형 렌더링 완료")
        return self.fig
