"""
주파수 스펙트럼 시각화

주파수 영역 스펙트럼을 시각화합니다.
"""

import librosa
import numpy as np

from src.analysis.result import AnalysisResult
from src.visualization.base import BaseVisualizer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SpectrumVisualizer(BaseVisualizer):
    """주파수 스펙트럼 시각화기"""

    def render(self, result: AnalysisResult = None, frame_index: int = None, **kwargs):
        """
        주파수 스펙트럼 렌더링

        Args:
            result: 분석 결과
            frame_index: 프레임 인덱스 (None이면 평균)
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        if result is None or not result.spectral:
            raise ValueError("분석 결과가 필요합니다")

        # STFT 데이터
        stft = result.spectral.get("stft")
        if stft is None:
            raise ValueError("STFT 데이터가 없습니다")

        # Figure 생성
        self.create_figure()

        # 스펙트럼 계산
        magnitude = np.abs(stft)

        if frame_index is not None:
            # 특정 프레임
            spectrum = magnitude[:, frame_index]
            title = f"주파수 스펙트럼 (Frame {frame_index})"
        else:
            # 평균 스펙트럼
            spectrum = np.mean(magnitude, axis=1)
            title = "평균 주파수 스펙트럼"

        # 주파수 축
        freqs = librosa.fft_frequencies(sr=result.sample_rate)

        # dB 스케일 변환
        spectrum_db = librosa.amplitude_to_db(spectrum, ref=np.max)

        # 스펙트럼 그리기
        self.ax.plot(freqs, spectrum_db, color=self.primary_color, linewidth=1.5)
        self.ax.fill_between(freqs, spectrum_db, alpha=0.3, color=self.primary_color)

        # 레이블 및 제목
        self.set_title(title)
        self.set_labels("주파수 (Hz)", "크기 (dB)")
        self.add_grid()

        # x축 로그 스케일 (선택)
        if kwargs.get("log_scale", False):
            self.ax.set_xscale("log")

        logger.info("주파수 스펙트럼 렌더링 완료")
        return self.fig
