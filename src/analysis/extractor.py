"""
특성 추출 통합 시스템

모든 분석 모듈을 통합하여 오디오 특성을 추출합니다.
"""

from collections.abc import Callable
from pathlib import Path

import librosa
import numpy as np

from src.analysis.harmony import HarmonicAnalyzer
from src.analysis.metadata import MetadataExtractor
from src.analysis.result import AnalysisResult
from src.analysis.rhythm import RhythmAnalyzer
from src.analysis.spectral import SpectralAnalyzer
from src.analysis.timbre import TimbreAnalyzer
from src.core.config import config
from src.core.exceptions import AudioException, AudioFileNotFoundError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class FeatureExtractor:
    """
    특성 추출기

    모든 분석 모듈을 통합하여 오디오 파일로부터 특성을 추출합니다.
    """

    def __init__(self, config_override: dict = None):
        """
        FeatureExtractor 초기화

        Args:
            config_override: 설정 오버라이드
        """
        cfg = config_override or {}

        self.sample_rate = cfg.get("sample_rate", config.get("audio.sample_rate", 44100))

        # 분석기 초기화
        self.spectral_analyzer = SpectralAnalyzer(cfg)
        self.rhythm_analyzer = RhythmAnalyzer(cfg)
        self.harmonic_analyzer = HarmonicAnalyzer(cfg)
        self.timbre_analyzer = TimbreAnalyzer(cfg)
        self.metadata_extractor = MetadataExtractor()

        logger.info("FeatureExtractor 초기화 완료")

    def extract(
        self,
        file_path: Path | str,
        features: list[str] | None = None,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> AnalysisResult:
        """
        오디오 파일로부터 특성 추출

        Args:
            file_path: 오디오 파일 경로
            features: 추출할 특성 리스트 (None이면 전체)
            progress_callback: 진행률 콜백 함수 (feature_name, progress)

        Returns:
            AnalysisResult

        Raises:
            AudioFileNotFoundError: 파일을 찾을 수 없는 경우
            AudioException: 분석 실패
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise AudioFileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        logger.info(f"특성 추출 시작: {file_path.name}")

        # 기본 특성 목록
        if features is None:
            features = ["spectral", "rhythm", "harmonic", "timbre", "metadata"]

        try:
            # 메타데이터 추출
            if "metadata" in features:
                self._report_progress(progress_callback, "metadata", 0.0)
                metadata = self.metadata_extractor.extract(file_path)
                self._report_progress(progress_callback, "metadata", 1.0)
            else:
                metadata = {}

            # 오디오 로드
            logger.info("오디오 로드 중...")
            y, sr = librosa.load(str(file_path), sr=self.sample_rate)
            duration = librosa.get_duration(y=y, sr=sr)

            # 분석 결과 초기화
            result = AnalysisResult(
                file_path=file_path,
                duration=duration,
                sample_rate=sr,
                metadata=metadata,
            )

            # 스펙트럼 분석
            if "spectral" in features:
                self._report_progress(progress_callback, "spectral", 0.0)
                result.spectral = self.spectral_analyzer.analyze(y, sr)
                self._report_progress(progress_callback, "spectral", 1.0)

            # 리듬 분석
            if "rhythm" in features:
                self._report_progress(progress_callback, "rhythm", 0.0)
                result.rhythm = self.rhythm_analyzer.analyze(y, sr)
                self._report_progress(progress_callback, "rhythm", 1.0)

            # 화성 분석
            if "harmonic" in features:
                self._report_progress(progress_callback, "harmonic", 0.0)
                result.harmonic = self.harmonic_analyzer.analyze(y, sr)
                self._report_progress(progress_callback, "harmonic", 1.0)

            # 음색 분석
            if "timbre" in features:
                self._report_progress(progress_callback, "timbre", 0.0)
                result.timbre = self.timbre_analyzer.analyze(y, sr)
                self._report_progress(progress_callback, "timbre", 1.0)

            logger.info(f"특성 추출 완료: {file_path.name}")
            return result

        except Exception as e:
            logger.error(f"특성 추출 실패: {e}", exc_info=True)
            raise AudioException(f"특성 추출 실패: {e}") from e

    def extract_realtime(self, audio_data: np.ndarray, sr: int, features: list[str] | None = None) -> dict:
        """
        실시간 오디오 데이터로부터 특성 추출

        Args:
            audio_data: 오디오 신호
            sr: 샘플링 레이트
            features: 추출할 특성 리스트

        Returns:
            특성 딕셔너리
        """
        if features is None:
            features = ["spectral", "rhythm"]

        result = {}

        if "spectral" in features:
            result["spectral"] = self.spectral_analyzer.analyze(audio_data, sr)

        if "rhythm" in features:
            result["rhythm"] = self.rhythm_analyzer.analyze(audio_data, sr)

        if "harmonic" in features:
            result["harmonic"] = self.harmonic_analyzer.analyze(audio_data, sr)

        if "timbre" in features:
            result["timbre"] = self.timbre_analyzer.analyze(audio_data, sr)

        return result

    def _report_progress(
        self,
        callback: Callable[[str, float], None] | None,
        feature_name: str,
        progress: float,
    ) -> None:
        """
        진행률 보고

        Args:
            callback: 콜백 함수
            feature_name: 특성 이름
            progress: 진행률 (0.0 ~ 1.0)
        """
        if callback:
            callback(feature_name, progress)
