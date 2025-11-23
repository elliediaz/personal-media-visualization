"""
리듬 분석

템포, 비트, 음 시작점 등 리듬 관련 특성을 분석합니다.
"""

from typing import Optional, Tuple

import librosa
import numpy as np

from src.core.config import config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RhythmAnalyzer:
    """
    리듬 분석기

    템포, 비트 추적, onset 감지 등을 수행합니다.
    """

    def __init__(self, config_override: dict = None):
        """
        RhythmAnalyzer 초기화

        Args:
            config_override: 설정 오버라이드
        """
        cfg = config_override or {}

        self.hop_size = cfg.get("hop_size", config.get("analysis.hop_size", 512))
        self.min_bpm = cfg.get("min_bpm", config.get("analysis.tempo.min_bpm", 60))
        self.max_bpm = cfg.get("max_bpm", config.get("analysis.tempo.max_bpm", 200))

        logger.debug(f"RhythmAnalyzer 초기화: BPM 범위={self.min_bpm}-{self.max_bpm}")

    def analyze(self, y: np.ndarray, sr: int) -> dict:
        """
        전체 리듬 분석 수행

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            리듬 특성 딕셔너리
        """
        logger.info("리듬 분석 시작")

        tempo, beats = self.track_beats(y, sr)
        onsets = self.detect_onsets(y, sr)

        result = {
            "tempo": tempo,
            "beats": beats,
            "beat_times": librosa.frames_to_time(beats, sr=sr, hop_length=self.hop_size),
            "onsets": onsets,
            "onset_times": librosa.frames_to_time(onsets, sr=sr, hop_length=self.hop_size),
            "onset_strength": self.compute_onset_strength(y, sr),
        }

        logger.info(f"리듬 분석 완료: 템포={tempo:.1f} BPM, 비트={len(beats)}개")
        return result

    def detect_tempo(self, y: np.ndarray, sr: int) -> float:
        """
        템포 감지

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            템포 (BPM)
        """
        tempo, _ = librosa.beat.beat_track(
            y=y, sr=sr, hop_length=self.hop_size, start_bpm=120, tightness=100
        )

        # 스칼라로 변환 (배열인 경우)
        if isinstance(tempo, np.ndarray):
            tempo = float(tempo)

        logger.debug(f"템포 감지: {tempo:.1f} BPM")
        return tempo

    def track_beats(self, y: np.ndarray, sr: int) -> Tuple[float, np.ndarray]:
        """
        비트 추적

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            (템포, 비트 프레임 위치)
        """
        tempo, beats = librosa.beat.beat_track(
            y=y, sr=sr, hop_length=self.hop_size, start_bpm=120, tightness=100
        )

        # 스칼라로 변환
        if isinstance(tempo, np.ndarray):
            tempo = float(tempo)

        logger.debug(f"비트 추적 완료: {len(beats)}개 비트")
        return tempo, beats

    def detect_onsets(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Onset (음 시작점) 감지

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            Onset 프레임 위치
        """
        onsets = librosa.onset.onset_detect(y=y, sr=sr, hop_length=self.hop_size, units="frames")

        logger.debug(f"Onset 감지 완료: {len(onsets)}개")
        return onsets

    def compute_onset_strength(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Onset strength envelope 계산

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            Onset strength 값
        """
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=self.hop_size)

        logger.debug(f"Onset strength 계산 완료: 최대={np.max(onset_env):.2f}")
        return onset_env

    def estimate_tempo_curve(self, y: np.ndarray, sr: int, win_length: int = 384) -> np.ndarray:
        """
        템포 변화 곡선 추정

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트
            win_length: 윈도우 길이

        Returns:
            시간에 따른 템포 값
        """
        tempogram = librosa.feature.tempogram(y=y, sr=sr, hop_length=self.hop_size, win_length=win_length)

        # 각 프레임에서 가장 강한 템포 추출
        tempo_curve = np.argmax(tempogram, axis=0)

        logger.debug(f"템포 곡선 추정 완료: shape={tempo_curve.shape}")
        return tempo_curve
