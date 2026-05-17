"""
오디오 API 엔드포인트

오디오 파일 관리 API
"""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from src.api.models import AudioInfo, AudioUploadResponse
from src.audio.formats import AudioFormat, AudioFormatNotSupportedError
from src.core.config import Config
from src.utils.logging import get_logger

logger = get_logger(__name__)
config = Config()

# API 라우터
router = APIRouter()

# 오디오 저장소 (실제로는 DB 사용)
audio_storage: dict[str, AudioInfo] = {}

# 업로드 디렉토리
UPLOAD_DIR = Path(config.get("api.upload_dir", "data/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_audio_duration(file_path: Path) -> float:
    """
    오디오 파일 재생 시간 가져오기

    Args:
        file_path: 파일 경로

    Returns:
        재생 시간 (초)
    """
    try:
        import librosa

        duration = librosa.get_duration(path=str(file_path))
        return float(duration)
    except Exception as e:
        logger.warning(f"재생 시간 추출 실패: {e}")
        return 0.0


def get_audio_info_from_file(file_path: Path, audio_id: str, filename: str) -> AudioInfo:
    """
    파일로부터 오디오 정보 추출

    Args:
        file_path: 파일 경로
        audio_id: 오디오 ID
        filename: 원본 파일명

    Returns:
        오디오 정보
    """
    try:
        import soundfile as sf

        # 기본 정보
        info = sf.info(str(file_path))
        duration = get_audio_duration(file_path)

        # 파일 포맷
        audio_format = AudioFormat.from_extension(file_path.suffix)

        return AudioInfo(
            id=audio_id,
            filename=filename,
            duration=duration,
            sample_rate=info.samplerate,
            channels=info.channels,
            format=audio_format.value,
            size=file_path.stat().st_size,
            created_at=datetime.now(),
        )

    except Exception as e:
        logger.error(f"오디오 정보 추출 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오디오 정보 추출 실패: {str(e)}",
        ) from e


@router.post("/upload", response_model=AudioUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio(file: UploadFile = File(...)):
    """
    오디오 파일 업로드

    Args:
        file: 업로드 파일

    Returns:
        업로드 결과
    """
    logger.info(f"오디오 업로드: {file.filename}")

    # 파일 검증
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일명이 없습니다",
        )

    # 확장자 검증
    try:
        file_ext = Path(file.filename).suffix
        AudioFormat.from_extension(file_ext)
    except (ValueError, AudioFormatNotSupportedError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 파일 형식: {file_ext}",
        ) from e

    # 파일 크기 제한 (100MB)
    max_size = config.get("api.max_upload_size", 100 * 1024 * 1024)

    # 고유 ID 생성
    audio_id = str(uuid4())

    # 파일 저장
    file_path = UPLOAD_DIR / f"{audio_id}{file_ext}"

    try:
        with file_path.open("wb") as buffer:
            content = await file.read()

            # 크기 검증
            if len(content) > max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"파일 크기가 너무 큽니다 (최대 {max_size / 1024 / 1024:.0f}MB)",
                )

            buffer.write(content)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 저장 실패: {e}", exc_info=True)
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 저장 실패: {str(e)}",
        ) from e

    # 오디오 정보 추출
    try:
        audio_info = get_audio_info_from_file(file_path, audio_id, file.filename)
        audio_storage[audio_id] = audio_info

        logger.info(f"오디오 업로드 완료: {audio_id} ({file.filename})")

        return AudioUploadResponse(
            audio_id=audio_id,
            message="업로드 성공",
            info=audio_info,
        )

    except Exception:
        # 실패시 파일 삭제
        if file_path.exists():
            file_path.unlink()
        raise


@router.get("/{audio_id}", response_model=AudioInfo)
async def get_audio(audio_id: str):
    """
    오디오 정보 조회

    Args:
        audio_id: 오디오 ID

    Returns:
        오디오 정보
    """
    if audio_id not in audio_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"오디오를 찾을 수 없습니다: {audio_id}",
        )

    return audio_storage[audio_id]


@router.get("/{audio_id}/download")
async def download_audio(audio_id: str):
    """
    오디오 파일 다운로드

    Args:
        audio_id: 오디오 ID

    Returns:
        파일 응답
    """
    if audio_id not in audio_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"오디오를 찾을 수 없습니다: {audio_id}",
        )

    audio_info = audio_storage[audio_id]

    # 파일 경로
    audio_format = AudioFormat.from_extension(Path(audio_info.filename).suffix)
    file_path = UPLOAD_DIR / f"{audio_id}.{audio_format.value}"

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다",
        )

    return FileResponse(
        path=file_path,
        filename=audio_info.filename,
        media_type=f"audio/{audio_format.value}",
    )


@router.delete("/{audio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audio(audio_id: str):
    """
    오디오 파일 삭제

    Args:
        audio_id: 오디오 ID
    """
    if audio_id not in audio_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"오디오를 찾을 수 없습니다: {audio_id}",
        )

    audio_info = audio_storage[audio_id]

    # 파일 삭제
    audio_format = AudioFormat.from_extension(Path(audio_info.filename).suffix)
    file_path = UPLOAD_DIR / f"{audio_id}.{audio_format.value}"

    if file_path.exists():
        file_path.unlink()

    # 저장소에서 제거
    del audio_storage[audio_id]

    logger.info(f"오디오 삭제 완료: {audio_id}")


@router.get("/", response_model=list[AudioInfo])
async def list_audio():
    """
    오디오 목록 조회

    Returns:
        오디오 정보 목록
    """
    return list(audio_storage.values())
