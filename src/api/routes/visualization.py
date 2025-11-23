"""
시각화 API 엔드포인트

시각화 렌더링 API
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse

from src.api.models import (
    OutputFormat,
    PresetInfo,
    PresetsResponse,
    VisualizationRequest,
    VisualizationResponse,
    VisualizationType,
)
from src.api.routes.analysis import analysis_results, analysis_storage
from src.api.routes.audio import UPLOAD_DIR, audio_storage
from src.audio.formats import AudioFormat
from src.core.config import Config
from src.utils.logging import get_logger

logger = get_logger(__name__)
config = Config()

# API 라우터
router = APIRouter()

# 시각화 저장소
viz_storage: Dict[str, VisualizationResponse] = {}

# 렌더링 출력 디렉토리
OUTPUT_DIR = Path(config.get("api.output_dir", "output/api"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def render_visualization(
    viz_id: str,
    request: VisualizationRequest,
    result,
    audio_file: Path = None,
):
    """
    시각화 렌더링

    Args:
        viz_id: 시각화 ID
        request: 시각화 요청
        result: 분석 결과
        audio_file: 오디오 파일 경로
    """
    try:
        # 출력 파일 경로
        output_file = OUTPUT_DIR / f"{viz_id}.{request.output_format.value}"

        # Figsize 계산
        dpi = request.dpi
        figsize = (request.width / dpi, request.height / dpi)

        # 파라미터
        params = request.params or {}

        # 시각화 타입별 렌더링
        if request.viz_type == VisualizationType.WAVEFORM:
            from src.visualization.statistical.waveform import WaveformVisualizer

            with WaveformVisualizer() as viz:
                viz.create_figure(figsize=figsize)
                viz.render(result=result, **params)
                viz.save(output_file)

        elif request.viz_type == VisualizationType.SPECTROGRAM:
            from src.visualization.statistical.spectrogram import SpectrogramVisualizer

            with SpectrogramVisualizer() as viz:
                viz.create_figure(figsize=figsize)
                viz.render(result=result, **params)
                viz.save(output_file)

        elif request.viz_type == VisualizationType.MEL_SPECTROGRAM:
            from src.visualization.statistical.spectrogram import SpectrogramVisualizer

            with SpectrogramVisualizer() as viz:
                viz.create_figure(figsize=figsize)
                viz.render(result=result, mel=True, **params)
                viz.save(output_file)

        elif request.viz_type == VisualizationType.SPECTRUM:
            from src.visualization.statistical.spectrum import SpectrumVisualizer

            with SpectrumVisualizer() as viz:
                viz.create_figure(figsize=figsize)
                viz.render(result=result, **params)
                viz.save(output_file)

        elif request.viz_type == VisualizationType.FEATURES:
            from src.visualization.statistical.features import FeatureVisualizer

            features = params.get("features", ["energy", "centroid", "tempo"])
            with FeatureVisualizer() as viz:
                viz.render(result=result, features=features, figsize=figsize)
                viz.save(output_file)

        elif request.viz_type == VisualizationType.RHYTHM:
            from src.visualization.statistical.rhythm import RhythmVisualizer

            with RhythmVisualizer() as viz:
                viz.render(result=result, figsize=figsize, **params)
                viz.save(output_file)

        elif request.viz_type == VisualizationType.PARTICLES:
            from src.visualization.artistic.particles import ParticleVisualizer

            num_particles = params.get("num_particles", 2000)
            with ParticleVisualizer() as viz:
                viz.create_figure(figsize=figsize)
                viz.render(result, num_particles=num_particles, **params)
                viz.save(output_file)

        elif request.viz_type == VisualizationType.CIRCLES:
            from src.visualization.artistic.circles import CircleVisualizer

            num_circles = params.get("num_circles", 60)
            with CircleVisualizer() as viz:
                viz.create_figure(figsize=figsize)
                viz.render(result, num_circles=num_circles, **params)
                viz.save(output_file)

        elif request.viz_type == VisualizationType.WAVES:
            from src.visualization.artistic.waves import WaveInterferenceVisualizer

            resolution = params.get("resolution", 500)
            cmap = params.get("cmap", "twilight")
            with WaveInterferenceVisualizer() as viz:
                viz.create_figure(figsize=figsize)
                viz.render(result, resolution=resolution, cmap=cmap, **params)
                viz.save(output_file)

        else:
            raise ValueError(f"지원하지 않는 시각화 타입: {request.viz_type}")

        # 저장소 업데이트
        viz_storage[viz_id].file_path = str(output_file)
        viz_storage[viz_id].file_url = f"/api/v1/visualize/{viz_id}/download"

        logger.info(f"시각화 완료: {viz_id} ({request.viz_type})")

    except Exception as e:
        logger.error(f"시각화 렌더링 실패: {e}", exc_info=True)
        raise


@router.post("/render", response_model=VisualizationResponse, status_code=status.HTTP_201_CREATED)
async def render(request: VisualizationRequest, background_tasks: BackgroundTasks):
    """
    시각화 렌더링 요청

    Args:
        request: 시각화 요청
        background_tasks: 백그라운드 태스크

    Returns:
        시각화 응답
    """
    logger.info(f"시각화 요청: {request.viz_type}")

    # 분석 결과 또는 오디오 확인
    result = None
    audio_file = None

    if request.analysis_id:
        # 분석 결과 사용
        if request.analysis_id not in analysis_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"분석 결과를 찾을 수 없습니다: {request.analysis_id}",
            )

        result = analysis_results[request.analysis_id]

    elif request.audio_id:
        # 오디오 파일에서 직접 분석
        if request.audio_id not in audio_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"오디오를 찾을 수 없습니다: {request.audio_id}",
            )

        audio_info = audio_storage[request.audio_id]
        audio_format = AudioFormat.from_extension(Path(audio_info.filename).suffix)
        audio_file = UPLOAD_DIR / f"{request.audio_id}.{audio_format.value}"

        if not audio_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="파일을 찾을 수 없습니다",
            )

        # 즉시 분석
        from src.analysis.extractor import FeatureExtractor

        extractor = FeatureExtractor()
        result = extractor.extract(audio_file)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="audio_id 또는 analysis_id가 필요합니다",
        )

    # 시각화 ID 생성
    viz_id = str(uuid4())

    # 응답 생성
    response = VisualizationResponse(
        viz_id=viz_id,
        audio_id=request.audio_id,
        analysis_id=request.analysis_id,
        viz_type=request.viz_type,
        output_format=request.output_format,
        file_path=None,
        file_url=None,
        width=request.width,
        height=request.height,
        created_at=datetime.now(),
    )

    viz_storage[viz_id] = response

    # 백그라운드에서 렌더링
    background_tasks.add_task(
        render_visualization,
        viz_id,
        request,
        result,
        audio_file,
    )

    logger.info(f"시각화 시작: {viz_id}")

    return response


@router.get("/{viz_id}", response_model=VisualizationResponse)
async def get_visualization(viz_id: str):
    """
    시각화 정보 조회

    Args:
        viz_id: 시각화 ID

    Returns:
        시각화 응답
    """
    if viz_id not in viz_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"시각화를 찾을 수 없습니다: {viz_id}",
        )

    return viz_storage[viz_id]


@router.get("/{viz_id}/download")
async def download_visualization(viz_id: str):
    """
    시각화 파일 다운로드

    Args:
        viz_id: 시각화 ID

    Returns:
        파일 응답
    """
    if viz_id not in viz_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"시각화를 찾을 수 없습니다: {viz_id}",
        )

    viz_info = viz_storage[viz_id]

    if not viz_info.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="렌더링이 완료되지 않았습니다",
        )

    file_path = Path(viz_info.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다",
        )

    # MIME 타입
    mime_types = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "svg": "image/svg+xml",
        "mp4": "video/mp4",
        "gif": "image/gif",
    }

    media_type = mime_types.get(viz_info.output_format.value, "application/octet-stream")

    return FileResponse(
        path=file_path,
        filename=f"{viz_id}.{viz_info.output_format.value}",
        media_type=media_type,
    )


@router.delete("/{viz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_visualization(viz_id: str):
    """
    시각화 삭제

    Args:
        viz_id: 시각화 ID
    """
    if viz_id not in viz_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"시각화를 찾을 수 없습니다: {viz_id}",
        )

    viz_info = viz_storage[viz_id]

    # 파일 삭제
    if viz_info.file_path:
        file_path = Path(viz_info.file_path)
        if file_path.exists():
            file_path.unlink()

    # 저장소에서 제거
    del viz_storage[viz_id]

    logger.info(f"시각화 삭제 완료: {viz_id}")


@router.get("/presets", response_model=PresetsResponse)
async def get_presets():
    """
    시각화 프리셋 목록 조회

    Returns:
        프리셋 목록
    """
    presets = [
        PresetInfo(
            name="기본 파형",
            description="기본 오디오 파형 시각화",
            viz_type=VisualizationType.WAVEFORM,
            params={},
        ),
        PresetInfo(
            name="Mel Spectrogram",
            description="Mel 스펙트로그램",
            viz_type=VisualizationType.MEL_SPECTROGRAM,
            params={},
        ),
        PresetInfo(
            name="에너지 파티클",
            description="에너지 기반 파티클 시각화",
            viz_type=VisualizationType.PARTICLES,
            params={"num_particles": 3000},
        ),
        PresetInfo(
            name="비트 동심원",
            description="비트 기반 동심원",
            viz_type=VisualizationType.CIRCLES,
            params={"num_circles": 80},
        ),
        PresetInfo(
            name="파동 간섭 (Plasma)",
            description="Plasma 컬러맵 파동 간섭",
            viz_type=VisualizationType.WAVES,
            params={"resolution": 600, "cmap": "plasma"},
        ),
        PresetInfo(
            name="파동 간섭 (Twilight)",
            description="Twilight 컬러맵 파동 간섭",
            viz_type=VisualizationType.WAVES,
            params={"resolution": 600, "cmap": "twilight"},
        ),
    ]

    return PresetsResponse(presets=presets, count=len(presets))


@router.get("/", response_model=List[VisualizationResponse])
async def list_visualizations():
    """
    시각화 목록 조회

    Returns:
        시각화 응답 목록
    """
    return list(viz_storage.values())
