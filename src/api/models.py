"""
API 모델

FastAPI 요청/응답을 위한 Pydantic 모델
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ===== Enums =====


class VisualizationType(str, Enum):
    """시각화 타입"""

    WAVEFORM = "waveform"
    SPECTROGRAM = "spectrogram"
    MEL_SPECTROGRAM = "mel_spectrogram"
    SPECTRUM = "spectrum"
    FEATURES = "features"
    RHYTHM = "rhythm"
    PARTICLES = "particles"
    CIRCLES = "circles"
    WAVES = "waves"


class AnalysisStatus(str, Enum):
    """분석 상태"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OutputFormat(str, Enum):
    """출력 포맷"""

    PNG = "png"
    JPG = "jpg"
    SVG = "svg"
    MP4 = "mp4"
    GIF = "gif"


# ===== Request Models =====


class AudioUploadRequest(BaseModel):
    """오디오 업로드 요청"""

    filename: str = Field(..., description="파일명")
    content_type: str = Field(..., description="MIME 타입")


class AnalysisRequest(BaseModel):
    """분석 요청"""

    audio_id: str = Field(..., description="오디오 ID")
    features: Optional[List[str]] = Field(
        None, description="추출할 특성 목록 (None이면 전체)"
    )
    use_cache: bool = Field(True, description="캐시 사용 여부")


class VisualizationRequest(BaseModel):
    """시각화 요청"""

    audio_id: Optional[str] = Field(None, description="오디오 ID")
    analysis_id: Optional[str] = Field(None, description="분석 결과 ID")
    viz_type: VisualizationType = Field(..., description="시각화 타입")
    output_format: OutputFormat = Field(OutputFormat.PNG, description="출력 포맷")
    width: int = Field(1920, ge=320, le=7680, description="너비 (px)")
    height: int = Field(1080, ge=240, le=4320, description="높이 (px)")
    dpi: int = Field(100, ge=50, le=300, description="DPI")
    params: Optional[Dict[str, Any]] = Field(None, description="추가 파라미터")

    @field_validator("params")
    @classmethod
    def validate_params(cls, v):
        """파라미터 검증"""
        if v is None:
            return {}
        return v


class StreamRequest(BaseModel):
    """스트림 요청"""

    audio_id: str = Field(..., description="오디오 ID")
    buffer_size: int = Field(2048, ge=512, le=8192, description="버퍼 크기")
    sample_rate: int = Field(44100, description="샘플링 레이트")


# ===== Response Models =====


class AudioInfo(BaseModel):
    """오디오 정보"""

    id: str = Field(..., description="오디오 ID")
    filename: str = Field(..., description="파일명")
    duration: float = Field(..., description="재생 시간 (초)")
    sample_rate: int = Field(..., description="샘플링 레이트")
    channels: int = Field(..., description="채널 수")
    format: str = Field(..., description="파일 포맷")
    size: int = Field(..., description="파일 크기 (bytes)")
    created_at: datetime = Field(..., description="생성 시각")


class AudioUploadResponse(BaseModel):
    """오디오 업로드 응답"""

    audio_id: str = Field(..., description="오디오 ID")
    message: str = Field(..., description="메시지")
    info: Optional[AudioInfo] = Field(None, description="오디오 정보")


class FeatureData(BaseModel):
    """특성 데이터"""

    name: str = Field(..., description="특성 이름")
    shape: Optional[List[int]] = Field(None, description="데이터 형태")
    dtype: str = Field(..., description="데이터 타입")
    min_value: Optional[float] = Field(None, description="최소값")
    max_value: Optional[float] = Field(None, description="최대값")
    mean_value: Optional[float] = Field(None, description="평균값")


class AnalysisResponse(BaseModel):
    """분석 응답"""

    analysis_id: str = Field(..., description="분석 ID")
    audio_id: str = Field(..., description="오디오 ID")
    status: AnalysisStatus = Field(..., description="분석 상태")
    features: Optional[Dict[str, Any]] = Field(None, description="추출된 특성")
    feature_summary: Optional[List[FeatureData]] = Field(
        None, description="특성 요약"
    )
    duration: Optional[float] = Field(None, description="분석 소요 시간 (초)")
    error: Optional[str] = Field(None, description="에러 메시지")
    created_at: datetime = Field(..., description="생성 시각")
    completed_at: Optional[datetime] = Field(None, description="완료 시각")


class VisualizationResponse(BaseModel):
    """시각화 응답"""

    viz_id: str = Field(..., description="시각화 ID")
    audio_id: Optional[str] = Field(None, description="오디오 ID")
    analysis_id: Optional[str] = Field(None, description="분석 ID")
    viz_type: VisualizationType = Field(..., description="시각화 타입")
    output_format: OutputFormat = Field(..., description="출력 포맷")
    file_path: Optional[str] = Field(None, description="파일 경로")
    file_url: Optional[str] = Field(None, description="파일 URL")
    width: int = Field(..., description="너비")
    height: int = Field(..., description="높이")
    created_at: datetime = Field(..., description="생성 시각")


class PresetInfo(BaseModel):
    """프리셋 정보"""

    name: str = Field(..., description="프리셋 이름")
    description: str = Field(..., description="설명")
    viz_type: VisualizationType = Field(..., description="시각화 타입")
    params: Dict[str, Any] = Field(..., description="파라미터")


class PresetsResponse(BaseModel):
    """프리셋 목록 응답"""

    presets: List[PresetInfo] = Field(..., description="프리셋 목록")
    count: int = Field(..., description="프리셋 개수")


class HealthResponse(BaseModel):
    """헬스체크 응답"""

    status: str = Field(..., description="상태")
    version: str = Field(..., description="버전")
    timestamp: datetime = Field(..., description="시각")


class ErrorResponse(BaseModel):
    """에러 응답"""

    error: str = Field(..., description="에러 타입")
    message: str = Field(..., description="에러 메시지")
    details: Optional[Dict[str, Any]] = Field(None, description="상세 정보")
    timestamp: datetime = Field(..., description="시각")


# ===== WebSocket Models =====


class StreamMessage(BaseModel):
    """스트림 메시지"""

    type: str = Field(..., description="메시지 타입")
    timestamp: float = Field(..., description="타임스탬프")
    data: Dict[str, Any] = Field(..., description="데이터")


class AudioStreamData(BaseModel):
    """오디오 스트림 데이터"""

    frame_index: int = Field(..., description="프레임 인덱스")
    audio_data: List[float] = Field(..., description="오디오 데이터")
    sample_rate: int = Field(..., description="샘플링 레이트")


class FeatureStreamData(BaseModel):
    """특성 스트림 데이터"""

    frame_index: int = Field(..., description="프레임 인덱스")
    tempo: Optional[float] = Field(None, description="템포")
    energy: Optional[float] = Field(None, description="에너지")
    spectral_centroid: Optional[float] = Field(None, description="Spectral Centroid")
    pitch: Optional[float] = Field(None, description="피치")


class VisualizationStreamData(BaseModel):
    """시각화 스트림 데이터"""

    frame_index: int = Field(..., description="프레임 인덱스")
    viz_type: VisualizationType = Field(..., description="시각화 타입")
    data: Dict[str, Any] = Field(..., description="시각화 데이터")
