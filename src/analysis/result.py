"""
오디오 분석 결과 데이터 클래스

분석된 오디오 특성을 구조화하여 저장하고 관리합니다.
"""

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AnalysisResult:
    """
    오디오 분석 결과를 저장하는 데이터 클래스

    Attributes:
        file_path: 분석된 파일 경로
        duration: 오디오 길이 (초)
        sample_rate: 샘플링 레이트
        spectral: 스펙트럼 분석 결과
        rhythm: 리듬 분석 결과
        harmonic: 화성 분석 결과
        timbre: 음색 분석 결과
        metadata: 메타데이터
        timestamp: 분석 시각 (Unix timestamp)
    """

    file_path: Path
    duration: float
    sample_rate: int
    spectral: dict = field(default_factory=dict)
    rhythm: dict = field(default_factory=dict)
    harmonic: dict = field(default_factory=dict)
    timbre: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """
        딕셔너리로 변환

        Returns:
            분석 결과 딕셔너리
        """
        result = asdict(self)
        result["file_path"] = str(self.file_path)

        # numpy 배열을 리스트로 변환
        result = self._convert_numpy_to_list(result)

        return result

    def _convert_numpy_to_list(self, obj: Any) -> Any:
        """
        numpy 배열을 리스트로 재귀적으로 변환

        Args:
            obj: 변환할 객체

        Returns:
            변환된 객체
        """
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_to_list(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_to_list(item) for item in obj]
        else:
            return obj

    def to_json(self, output_path: Path | str) -> None:
        """
        JSON 파일로 저장

        Args:
            output_path: 저장할 파일 경로
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = self.to_dict()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"분석 결과를 JSON으로 저장: {output_path}")

    @classmethod
    def from_json(cls, input_path: Path | str) -> "AnalysisResult":
        """
        JSON 파일에서 로드

        Args:
            input_path: 로드할 파일 경로

        Returns:
            AnalysisResult 인스턴스
        """
        input_path = Path(input_path)

        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["file_path"] = Path(data["file_path"])

        return cls(**data)

    def get_feature(self, feature_path: str, default: Any = None) -> Any:
        """
        특정 특성값 가져오기 (점 표기법 지원)

        Args:
            feature_path: 특성 경로 (예: "spectral.mfcc")
            default: 기본값

        Returns:
            특성값 또는 기본값

        Examples:
            >>> result.get_feature("rhythm.tempo")
            120.0
            >>> result.get_feature("spectral.mfcc")
            array([...])
        """
        keys = feature_path.split(".")
        value = self

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            elif hasattr(value, key):
                value = getattr(value, key, default)
            else:
                return default

            if value is None:
                return default

        return value

    def has_feature(self, feature_path: str) -> bool:
        """
        특성 존재 여부 확인

        Args:
            feature_path: 특성 경로

        Returns:
            존재 여부
        """
        return self.get_feature(feature_path) is not None

    def summary(self) -> str:
        """
        분석 결과 요약

        Returns:
            요약 문자열
        """
        lines = [
            f"파일: {self.file_path.name}",
            f"길이: {self.duration:.2f}초",
            f"샘플레이트: {self.sample_rate}Hz",
            "",
            "분석 결과:",
        ]

        if self.spectral:
            lines.append(f"  - 스펙트럼: {len(self.spectral)}개 특성")
        if self.rhythm:
            tempo = self.rhythm.get("tempo")
            lines.append(f"  - 리듬: 템포 {tempo:.1f} BPM" if tempo else "  - 리듬: 분석됨")
        if self.harmonic:
            key = self.harmonic.get("key")
            lines.append(f"  - 화성: 키 {key}" if key else "  - 화성: 분석됨")
        if self.timbre:
            lines.append(f"  - 음색: {len(self.timbre)}개 특성")
        if self.metadata:
            title = self.metadata.get("title")
            artist = self.metadata.get("artist")
            if title and artist:
                lines.append(f"  - 메타: {artist} - {title}")
            elif title:
                lines.append(f"  - 메타: {title}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """문자열 표현"""
        return f"AnalysisResult(file={self.file_path.name}, duration={self.duration:.2f}s)"
