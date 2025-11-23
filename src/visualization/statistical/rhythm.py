"""
리듬 시각화

비트, onset 등 리듬 관련 정보를 시각화합니다.
"""

import librosa
import librosa.display
import numpy as np

from src.analysis.result import AnalysisResult
from src.visualization.base import BaseVisualizer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RhythmVisualizer(BaseVisualizer):
    """리듬 시각화기"""

    def render(self, result: AnalysisResult = None, audio_data: np.ndarray = None, **kwargs):
        """
        리듬 정보 렌더링

        Args:
            result: 분석 결과
            audio_data: 오디오 신호 (선택, 파형 오버레이용)
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        if result is None or not result.rhythm:
            raise ValueError("리듬 분석 결과가 필요합니다")

        # Figure 생성
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 1, figsize=(12, 8), dpi=self.dpi)

        # 1. Onset strength envelope
        ax1 = axes[0]
        onset_env = result.rhythm.get("onset_strength")

        if onset_env is not None:
            times = librosa.frames_to_time(np.arange(len(onset_env)), sr=result.sample_rate)
            ax1.plot(times, onset_env, color=self.primary_color, linewidth=1.5, label="Onset Strength")
            ax1.fill_between(times, onset_env, alpha=0.3, color=self.primary_color)

            # Onset 위치 표시
            onset_frames = result.rhythm.get("onsets")
            if onset_frames is not None and len(onset_frames) > 0:
                onset_times = librosa.frames_to_time(onset_frames, sr=result.sample_rate)
                ax1.vlines(onset_times, 0, onset_env.max(), color=self.secondary_color,
                          alpha=0.6, linestyle="--", linewidth=1, label="Onsets")

            ax1.legend(loc="upper right")
            ax1.set_title("Onset Detection", color=self.fg_color)
            ax1.set_xlabel("시간 (초)", color=self.fg_color)
            ax1.set_ylabel("Strength", color=self.fg_color)
            ax1.set_facecolor(self.bg_color)
            ax1.tick_params(colors=self.fg_color)
            ax1.grid(True, alpha=0.3, linestyle="--", color=self.fg_color)

            for spine in ax1.spines.values():
                spine.set_color(self.fg_color)

        # 2. 비트 추적
        ax2 = axes[1]

        # 파형 표시 (있는 경우)
        if audio_data is not None:
            times_audio = librosa.times_like(audio_data, sr=result.sample_rate)
            ax2.plot(times_audio, audio_data, color=self.fg_color, alpha=0.3, linewidth=0.5)

        # 비트 위치 표시
        beat_times = result.rhythm.get("beat_times")
        tempo = result.rhythm.get("tempo", 0)

        if beat_times is not None and len(beat_times) > 0:
            ax2.vlines(beat_times, -1, 1, color=self.secondary_color,
                      alpha=0.8, linewidth=2, label=f"Beats (Tempo: {tempo:.1f} BPM)")

            ax2.legend(loc="upper right")

        ax2.set_title("Beat Tracking", color=self.fg_color)
        ax2.set_xlabel("시간 (초)", color=self.fg_color)
        ax2.set_ylabel("진폭", color=self.fg_color)
        ax2.set_ylim([-1.1, 1.1])
        ax2.set_facecolor(self.bg_color)
        ax2.tick_params(colors=self.fg_color)
        ax2.grid(True, alpha=0.3, linestyle="--", color=self.fg_color)

        for spine in ax2.spines.values():
            spine.set_color(self.fg_color)

        plt.tight_layout()
        self.fig = fig

        logger.info("리듬 시각화 렌더링 완료")
        return self.fig
