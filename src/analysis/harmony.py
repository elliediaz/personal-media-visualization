"""
화성 분석

피치, 크로마, 키 감지 등 화성 관련 특성을 분석합니다.
"""


import librosa
import numpy as np

from src.core.config import config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class HarmonicAnalyzer:
    """
    화성 분석기

    피치, 크로마, 키 등을 분석합니다.
    """

    def __init__(self, config_override: dict = None):
        """
        HarmonicAnalyzer 초기화

        Args:
            config_override: 설정 오버라이드
        """
        cfg = config_override or {}

        self.hop_size = cfg.get("hop_size", config.get("analysis.hop_size", 512))
        self.frame_size = cfg.get("frame_size", config.get("analysis.frame_size", 2048))

        logger.debug("HarmonicAnalyzer 초기화 완료")

    def analyze(self, y: np.ndarray, sr: int) -> dict:
        """
        전체 화성 분석 수행

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            화성 특성 딕셔너리
        """
        logger.info("화성 분석 시작")

        result = {
            "chroma_stft": self.extract_chroma_stft(y, sr),
            "chroma_cqt": self.extract_chroma_cqt(y, sr),
            "chroma_cens": self.extract_chroma_cens(y, sr),
            "tonnetz": self.extract_tonnetz(y, sr),
            "key": self.detect_key(y, sr),
        }

        # 피치 추출 (계산 비용이 높으므로 선택적)
        try:
            pitch, voiced_flag, voiced_prob = self.extract_pitch(y, sr)
            result["pitch"] = pitch
            result["voiced_flag"] = voiced_flag
            result["voiced_probability"] = voiced_prob
        except Exception as e:
            logger.warning(f"피치 추출 실패: {e}")
            result["pitch"] = None

        logger.info(f"화성 분석 완료: 키={result['key']}")
        return result

    def extract_pitch(self, y: np.ndarray, sr: int) -> tuple:
        """
        피치 추출 (pYIN 알고리즘)

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            (피치 값, voiced flag, voiced probability)
        """
        f0, voiced_flag, voiced_prob = librosa.pyin(
            y,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr,
            hop_length=self.hop_size,
        )

        logger.debug(f"피치 추출 완료: 평균 F0={np.nanmean(f0):.2f}Hz")
        return f0, voiced_flag, voiced_prob

    def extract_chroma_stft(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Chroma STFT 추출

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            Chroma 특성 (12 x frames)
        """
        chroma = librosa.feature.chroma_stft(
            y=y, sr=sr, n_fft=self.frame_size, hop_length=self.hop_size
        )

        logger.debug(f"Chroma STFT 추출 완료: shape={chroma.shape}")
        return chroma

    def extract_chroma_cqt(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Chroma CQT (Constant-Q Transform) 추출

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            Chroma CQT 특성
        """
        chroma_cqt = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=self.hop_size)

        logger.debug(f"Chroma CQT 추출 완료: shape={chroma_cqt.shape}")
        return chroma_cqt

    def extract_chroma_cens(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Chroma CENS (Chroma Energy Normalized) 추출

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            Chroma CENS 특성
        """
        chroma_cens = librosa.feature.chroma_cens(y=y, sr=sr, hop_length=self.hop_size)

        logger.debug(f"Chroma CENS 추출 완료: shape={chroma_cens.shape}")
        return chroma_cens

    def extract_tonnetz(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Tonnetz (Tonal Centroid Features) 추출

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            Tonnetz 특성
        """
        tonnetz = librosa.feature.tonnetz(y=y, sr=sr)

        logger.debug(f"Tonnetz 추출 완료: shape={tonnetz.shape}")
        return tonnetz

    def detect_key(self, y: np.ndarray, sr: int) -> str:
        """
        키 감지 (간단한 크로마 기반 추정)

        Args:
            y: 오디오 신호
            sr: 샘플링 레이트

        Returns:
            추정된 키 (예: "C major", "A minor")
        """
        # Chroma 추출
        chroma = self.extract_chroma_stft(y, sr)

        # 평균 크로마 프로파일
        chroma_profile = np.mean(chroma, axis=1)

        # 가장 강한 피치 클래스
        dominant_pitch_class = np.argmax(chroma_profile)

        # 피치 클래스를 노트로 변환
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        key_note = note_names[dominant_pitch_class]

        # 장/단조 추정 (간단한 휴리스틱)
        # 3번째 음(장3도)과 b3(단3도)의 세기 비교
        major_third = (dominant_pitch_class + 4) % 12
        minor_third = (dominant_pitch_class + 3) % 12

        is_major = chroma_profile[major_third] > chroma_profile[minor_third]
        mode = "major" if is_major else "minor"

        detected_key = f"{key_note} {mode}"
        logger.debug(f"키 감지: {detected_key}")

        return detected_key

    def get_pitch_statistics(self, pitch: np.ndarray) -> dict:
        """
        피치 통계 계산

        Args:
            pitch: 피치 배열

        Returns:
            통계값 딕셔너리
        """
        # NaN 제거
        valid_pitch = pitch[~np.isnan(pitch)]

        if len(valid_pitch) == 0:
            return {
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "voiced_ratio": 0.0,
            }

        return {
            "mean": float(np.mean(valid_pitch)),
            "std": float(np.std(valid_pitch)),
            "min": float(np.min(valid_pitch)),
            "max": float(np.max(valid_pitch)),
            "voiced_ratio": float(len(valid_pitch) / len(pitch)),
        }
