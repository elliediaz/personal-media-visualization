"""
음색 분석

음색 관련 특성을 분석합니다.
"""

import librosa
import numpy as np

from src.core.config import config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TimbreAnalyzer:
    """음색 분석기"""

    def __init__(self, config_override: dict = None):
        """
        TimbreAnalyzer 초기화

        Args:
            config_override: 설정 오버라이드
        """
        cfg = config_override or {}

        self.hop_size = cfg.get("hop_size", config.get("analysis.hop_size", 512))
        self.frame_size = cfg.get("frame_size", config.get("analysis.frame_size", 2048))

        logger.debug("TimbreAnalyzer 초기화 완료")

    def analyze(self, y: np.ndarray, sr: int) -> dict:
        """
        전체 음색 분석 수행

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            음색 특성 딕셔너리
        """
        logger.info("음색 분석 시작")

        # SpectralAnalyzer와 중복되지 않는 특성만 추출
        result = {
            "poly_features": self.extract_poly_features(y, sr),
            "rms_energy": self.compute_rms_energy(y),
        }

        logger.info("음색 분석 완료")
        return result

    def extract_poly_features(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Polynomial features 추출

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            Polynomial features
        """
        S = np.abs(librosa.stft(y, n_fft=self.frame_size, hop_length=self.hop_size))
        poly_features = librosa.feature.poly_features(S=S, sr=sr, order=1)

        logger.debug(f"Polynomial features 추출 완료: shape={poly_features.shape}")
        return poly_features

    def compute_rms_energy(self, y: np.ndarray) -> np.ndarray:
        """
        RMS (Root Mean Square) 에너지 계산

        Args:
            y: 오디오 신호

        Returns:
            RMS 에너지 값
        """
        rms = librosa.feature.rms(y=y, frame_length=self.frame_size, hop_length=self.hop_size)[0]

        logger.debug(f"RMS 에너지 계산 완료: 평균={np.mean(rms):.4f}")
        return rms
