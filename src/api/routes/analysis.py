"""
분석 API 엔드포인트

오디오 분석 API
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import numpy as np
from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from src.analysis.extractor import FeatureExtractor
from src.analysis.result import AnalysisResult
from src.api.models import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatus,
    FeatureData,
)
from src.api.routes.audio import UPLOAD_DIR, audio_storage
from src.audio.formats import AudioFormat
from src.core.config import Config
from src.utils.logging import get_logger

logger = get_logger(__name__)
config = Config()

# API 라우터
router = APIRouter()

# 분석 결과 저장소 (실제로는 DB 사용)
analysis_storage: Dict[str, AnalysisResponse] = {}
analysis_results: Dict[str, AnalysisResult] = {}


def create_feature_summary(result: AnalysisResult) -> List[FeatureData]:
    """
    특성 요약 생성

    Args:
        result: 분석 결과

    Returns:
        특성 데이터 목록
    """
    summaries = []

    # Spectral features
    for key, value in result.spectral.items():
        if isinstance(value, np.ndarray):
            summaries.append(
                FeatureData(
                    name=f"spectral.{key}",
                    shape=list(value.shape),
                    dtype=str(value.dtype),
                    min_value=float(np.min(value)),
                    max_value=float(np.max(value)),
                    mean_value=float(np.mean(value)),
                )
            )

    # Rhythm features
    for key, value in result.rhythm.items():
        if isinstance(value, np.ndarray):
            summaries.append(
                FeatureData(
                    name=f"rhythm.{key}",
                    shape=list(value.shape),
                    dtype=str(value.dtype),
                    min_value=float(np.min(value)),
                    max_value=float(np.max(value)),
                    mean_value=float(np.mean(value)),
                )
            )
        elif isinstance(value, (int, float)):
            summaries.append(
                FeatureData(
                    name=f"rhythm.{key}",
                    shape=None,
                    dtype="scalar",
                    min_value=float(value),
                    max_value=float(value),
                    mean_value=float(value),
                )
            )

    # Harmonic features
    for key, value in result.harmonic.items():
        if isinstance(value, np.ndarray):
            summaries.append(
                FeatureData(
                    name=f"harmonic.{key}",
                    shape=list(value.shape),
                    dtype=str(value.dtype),
                    min_value=float(np.min(value)),
                    max_value=float(np.max(value)),
                    mean_value=float(np.mean(value)),
                )
            )

    # Timbre features
    for key, value in result.timbre.items():
        if isinstance(value, np.ndarray):
            summaries.append(
                FeatureData(
                    name=f"timbre.{key}",
                    shape=list(value.shape),
                    dtype=str(value.dtype),
                    min_value=float(np.min(value)),
                    max_value=float(np.max(value)),
                    mean_value=float(np.mean(value)),
                )
            )

    return summaries


async def run_analysis(
    analysis_id: str,
    audio_id: str,
    file_path: Path,
    features: Optional[List[str]] = None,
):
    """
    백그라운드 분석 실행

    Args:
        analysis_id: 분석 ID
        audio_id: 오디오 ID
        file_path: 파일 경로
        features: 특성 목록
    """
    try:
        # 상태 업데이트
        analysis_storage[analysis_id].status = AnalysisStatus.PROCESSING

        # 분석 실행
        start_time = time.time()
        extractor = FeatureExtractor()

        result = extractor.extract(file_path, features=features)

        duration = time.time() - start_time

        # 특성 요약 생성
        feature_summary = create_feature_summary(result)

        # 결과 저장
        analysis_results[analysis_id] = result

        # 상태 업데이트
        analysis_storage[analysis_id] = AnalysisResponse(
            analysis_id=analysis_id,
            audio_id=audio_id,
            status=AnalysisStatus.COMPLETED,
            features=result.to_dict(),
            feature_summary=feature_summary,
            duration=duration,
            error=None,
            created_at=analysis_storage[analysis_id].created_at,
            completed_at=datetime.now(),
        )

        logger.info(f"분석 완료: {analysis_id} ({duration:.2f}초)")

    except Exception as e:
        logger.error(f"분석 실패: {e}", exc_info=True)

        # 에러 상태 업데이트
        analysis_storage[analysis_id].status = AnalysisStatus.FAILED
        analysis_storage[analysis_id].error = str(e)


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_audio(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    오디오 분석 요청

    Args:
        request: 분석 요청
        background_tasks: 백그라운드 태스크

    Returns:
        분석 응답
    """
    logger.info(f"분석 요청: {request.audio_id}")

    # 오디오 확인
    if request.audio_id not in audio_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"오디오를 찾을 수 없습니다: {request.audio_id}",
        )

    audio_info = audio_storage[request.audio_id]

    # 파일 경로
    audio_format = AudioFormat.from_extension(Path(audio_info.filename).suffix)
    file_path = UPLOAD_DIR / f"{request.audio_id}.{audio_format.value}"

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다",
        )

    # 분석 ID 생성
    analysis_id = str(uuid4())

    # 초기 응답 생성
    response = AnalysisResponse(
        analysis_id=analysis_id,
        audio_id=request.audio_id,
        status=AnalysisStatus.PENDING,
        features=None,
        feature_summary=None,
        duration=None,
        error=None,
        created_at=datetime.now(),
        completed_at=None,
    )

    analysis_storage[analysis_id] = response

    # 백그라운드에서 분석 실행
    background_tasks.add_task(
        run_analysis,
        analysis_id,
        request.audio_id,
        file_path,
        request.features,
    )

    logger.info(f"분석 시작: {analysis_id}")

    return response


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str):
    """
    분석 결과 조회

    Args:
        analysis_id: 분석 ID

    Returns:
        분석 응답
    """
    if analysis_id not in analysis_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"분석 결과를 찾을 수 없습니다: {analysis_id}",
        )

    return analysis_storage[analysis_id]


@router.get("/{analysis_id}/features", response_model=Dict)
async def get_analysis_features(
    analysis_id: str,
    feature_path: Optional[str] = None,
):
    """
    분석 특성 조회

    Args:
        analysis_id: 분석 ID
        feature_path: 특성 경로 (예: "spectral.centroid")

    Returns:
        특성 데이터
    """
    if analysis_id not in analysis_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"분석 결과를 찾을 수 없습니다: {analysis_id}",
        )

    analysis = analysis_storage[analysis_id]

    if analysis.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"분석이 완료되지 않았습니다: {analysis.status}",
        )

    if analysis_id not in analysis_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="분석 결과 데이터를 찾을 수 없습니다",
        )

    result = analysis_results[analysis_id]

    # 특정 특성 조회
    if feature_path:
        feature_value = result.get_feature(feature_path)

        if feature_value is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"특성을 찾을 수 없습니다: {feature_path}",
            )

        # numpy 배열을 리스트로 변환
        if isinstance(feature_value, np.ndarray):
            feature_value = feature_value.tolist()

        return {
            "feature_path": feature_path,
            "value": feature_value,
        }

    # 전체 특성 반환
    return result.to_dict()


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(analysis_id: str):
    """
    분석 결과 삭제

    Args:
        analysis_id: 분석 ID
    """
    if analysis_id not in analysis_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"분석 결과를 찾을 수 없습니다: {analysis_id}",
        )

    # 저장소에서 제거
    del analysis_storage[analysis_id]

    if analysis_id in analysis_results:
        del analysis_results[analysis_id]

    logger.info(f"분석 삭제 완료: {analysis_id}")


@router.get("/", response_model=List[AnalysisResponse])
async def list_analyses(audio_id: Optional[str] = None):
    """
    분석 목록 조회

    Args:
        audio_id: 오디오 ID (필터링)

    Returns:
        분석 응답 목록
    """
    analyses = list(analysis_storage.values())

    # 오디오 ID 필터링
    if audio_id:
        analyses = [a for a in analyses if a.audio_id == audio_id]

    return analyses
