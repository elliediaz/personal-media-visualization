"""
스펙트로그램 시각화

STFT, Mel-spectrogram 등을 시각화합니다.
"""

import librosa
import librosa.display
import numpy as np
from pathlib import Path

from src.analysis.result import AnalysisResult
from src.visualization.base import BaseVisualizer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SpectrogramVisualizer(BaseVisualizer):
    """스펙트로그램 시각화기"""

    def render(
        self,
        result: AnalysisResult = None,
        spec_type: str = "mel",
        **kwargs
    ):
        """
        스펙트로그램 렌더링

        Args:
            result: 분석 결과
            spec_type: 스펙트로그램 타입 ("mel", "stft")
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        if result is None or not result.spectral:
            raise ValueError("분석 결과가 필요합니다")

        # Figure 생성
        self.create_figure()

        # 스펙트로그램 데이터 가져오기
        if spec_type == "mel":
            spec_data = result.spectral.get("mel_spectrogram")
            title = "Mel-Spectrogram"
            y_axis = "mel"
        elif spec_type == "stft":
            stft = result.spectral.get("stft")
            spec_data = librosa.amplitude_to_db(np.abs(stft), ref=np.max)
            title = "STFT Spectrogram"
            y_axis = "hz"
        else:
            raise ValueError(f"지원하지 않는 스펙트로그램 타입: {spec_type}")

        if spec_data is None:
            raise ValueError(f"{spec_type} 스펙트로그램 데이터가 없습니다")

        # 컬러맵
        cmap = kwargs.get("cmap", "viridis")

        # 스펙트로그램 표시
        img = librosa.display.specshow(
            spec_data,
            sr=result.sample_rate,
            x_axis="time",
            y_axis=y_axis,
            cmap=cmap,
            ax=self.ax
        )

        # 컬러바 추가
        cbar = self.fig.colorbar(img, ax=self.ax, format="%+2.0f dB")
        cbar.ax.yaxis.set_tick_params(color=self.fg_color)
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=self.fg_color)

        # 제목 및 레이블
        self.set_title(title)
        self.set_labels("시간 (초)", "주파수 (Hz)" if y_axis == "hz" else "Mel")

        logger.info(f"{title} 렌더링 완료")
        return self.fig
