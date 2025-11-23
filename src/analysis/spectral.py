"""
스펙트럼 분석

오디오 신호의 주파수 영역 특성을 분석합니다.
"""

from typing import Optional

import librosa
import numpy as np

from src.core.config import config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SpectralAnalyzer:
    """
    스펙트럼 분석기

    STFT, Mel-spectrogram, MFCC 등 주파수 영역 특성을 추출합니다.
    """

    def __init__(self, config_override: dict = None):
        """
        SpectralAnalyzer 초기화

        Args:
            config_override: 설정 오버라이드
        """
        cfg = config_override or {}

        self.frame_size = cfg.get("frame_size", config.get("analysis.frame_size", 2048))
        self.hop_size = cfg.get("hop_size", config.get("analysis.hop_size", 512))
        self.n_mels = cfg.get("n_mels", config.get("analysis.mel.n_mels", 128))
        self.n_mfcc = cfg.get("n_mfcc", config.get("analysis.mfcc.n_mfcc", 13))
        self.fmin = cfg.get("fmin", config.get("analysis.mel.fmin", 20))
        self.fmax = cfg.get("fmax", config.get("analysis.mel.fmax", 20000))

        logger.debug(
            f"SpectralAnalyzer 초기화: frame={self.frame_size}, "
            f"hop={self.hop_size}, n_mels={self.n_mels}"
        )

    def analyze(self, y: np.ndarray, sr: int) -> dict:
        """
        전체 스펙트럼 분석 수행

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            스펙트럼 특성 딕셔너리
        """
        logger.info("스펙트럼 분석 시작")

        result = {
            "stft": self.compute_stft(y, sr),
            "mel_spectrogram": self.compute_mel_spectrogram(y, sr),
            "mfcc": self.compute_mfcc(y, sr),
            "spectral_centroid": self.compute_spectral_centroid(y, sr),
            "spectral_rolloff": self.compute_spectral_rolloff(y, sr),
            "spectral_bandwidth": self.compute_spectral_bandwidth(y, sr),
            "spectral_contrast": self.compute_spectral_contrast(y, sr),
            "spectral_flatness": self.compute_spectral_flatness(y, sr),
            "zero_crossing_rate": self.compute_zero_crossing_rate(y),
        }

        logger.info("스펙트럼 분석 완료")
        return result

    def compute_stft(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        STFT (Short-Time Fourier Transform) 계산

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            STFT 행렬 (복소수)
        """
        stft = librosa.stft(y, n_fft=self.frame_size, hop_length=self.hop_size)
        logger.debug(f"STFT 계산 완료: shape={stft.shape}")
        return stft

    def compute_mel_spectrogram(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Mel-spectrogram 계산

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            Mel-spectrogram (dB 스케일)
        """
        mel_spec = librosa.feature.melspectrogram(
            y=y,
            sr=sr,
            n_fft=self.frame_size,
            hop_length=self.hop_size,
            n_mels=self.n_mels,
            fmin=self.fmin,
            fmax=self.fmax,
        )

        # dB 스케일로 변환
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        logger.debug(f"Mel-spectrogram 계산 완료: shape={mel_spec_db.shape}")
        return mel_spec_db

    def compute_mfcc(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        MFCC (Mel-Frequency Cepstral Coefficients) 계산

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            MFCC 계수
        """
        mfcc = librosa.feature.mfcc(
            y=y,
            sr=sr,
            n_mfcc=self.n_mfcc,
            n_fft=self.frame_size,
            hop_length=self.hop_size,
        )

        logger.debug(f"MFCC 계산 완료: shape={mfcc.shape}")
        return mfcc

    def compute_spectral_centroid(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Spectral centroid (스펙트럼 중심) 계산

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            Spectral centroid 값
        """
        centroid = librosa.feature.spectral_centroid(
            y=y, sr=sr, n_fft=self.frame_size, hop_length=self.hop_size
        )[0]

        logger.debug(f"Spectral centroid 계산 완료: 평균={np.mean(centroid):.2f}Hz")
        return centroid

    def compute_spectral_rolloff(self, y: np.ndarray, sr: int, roll_percent: float = 0.85) -> np.ndarray:
        """
        Spectral rolloff 계산

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트
            roll_percent: Rolloff 비율 (기본 0.85)

        Returns:
            Spectral rolloff 값
        """
        rolloff = librosa.feature.spectral_rolloff(
            y=y,
            sr=sr,
            n_fft=self.frame_size,
            hop_length=self.hop_size,
            roll_percent=roll_percent,
        )[0]

        logger.debug(f"Spectral rolloff 계산 완료: 평균={np.mean(rolloff):.2f}Hz")
        return rolloff

    def compute_spectral_bandwidth(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Spectral bandwidth 계산

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            Spectral bandwidth 값
        """
        bandwidth = librosa.feature.spectral_bandwidth(
            y=y, sr=sr, n_fft=self.frame_size, hop_length=self.hop_size
        )[0]

        logger.debug(f"Spectral bandwidth 계산 완료: 평균={np.mean(bandwidth):.2f}Hz")
        return bandwidth

    def compute_spectral_contrast(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Spectral contrast 계산

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            Spectral contrast 값
        """
        contrast = librosa.feature.spectral_contrast(
            y=y, sr=sr, n_fft=self.frame_size, hop_length=self.hop_size
        )

        logger.debug(f"Spectral contrast 계산 완료: shape={contrast.shape}")
        return contrast

    def compute_spectral_flatness(self, y: np.ndarray, sr: int = None) -> np.ndarray:
        """
        Spectral flatness 계산

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트 (미사용, 호환성 유지)

        Returns:
            Spectral flatness 값
        """
        flatness = librosa.feature.spectral_flatness(
            y=y, n_fft=self.frame_size, hop_length=self.hop_size
        )[0]

        logger.debug(f"Spectral flatness 계산 완료: 평균={np.mean(flatness):.4f}")
        return flatness

    def compute_zero_crossing_rate(self, y: np.ndarray) -> np.ndarray:
        """
        Zero-crossing rate 계산

        Args:
            y: 오디오 신호

        Returns:
            Zero-crossing rate 값
        """
        zcr = librosa.feature.zero_crossing_rate(y, frame_length=self.frame_size, hop_length=self.hop_size)[
            0
        ]

        logger.debug(f"Zero-crossing rate 계산 완료: 평균={np.mean(zcr):.4f}")
        return zcr

    def get_spectral_statistics(self, feature: np.ndarray) -> dict:
        """
        특성의 통계값 계산

        Args:
            feature: 특성 배열

        Returns:
            통계값 딕셔너리 (mean, std, min, max)
        """
        return {
            "mean": float(np.mean(feature)),
            "std": float(np.std(feature)),
            "min": float(np.min(feature)),
            "max": float(np.max(feature)),
        }
