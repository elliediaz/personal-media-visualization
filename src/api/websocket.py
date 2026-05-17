"""
WebSocket 엔드포인트

실시간 오디오/분석/시각화 스트리밍
"""

import asyncio
import time
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi.websockets import WebSocketState

from src.analysis.extractor import FeatureExtractor
from src.api.models import (
    AudioStreamData,
    FeatureStreamData,
    StreamMessage,
    VisualizationStreamData,
    VisualizationType,
)
from src.api.routes.audio import UPLOAD_DIR, audio_storage
from src.audio.formats import AudioFormat
from src.core.config import Config
from src.utils.logging import get_logger

logger = get_logger(__name__)
config = Config()

# WebSocket 라우터
router = APIRouter()


class ConnectionManager:
    """WebSocket 연결 관리자"""

    def __init__(self):
        """초기화"""
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        클라이언트 연결

        Args:
            websocket: WebSocket 연결
            client_id: 클라이언트 ID
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket 연결: {client_id}")

    def disconnect(self, client_id: str):
        """
        클라이언트 연결 해제

        Args:
            client_id: 클라이언트 ID
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket 연결 해제: {client_id}")

    async def send_message(self, message: StreamMessage, client_id: str):
        """
        메시지 전송

        Args:
            message: 스트림 메시지
            client_id: 클라이언트 ID
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(message.model_dump())


manager = ConnectionManager()


@router.websocket("/ws/audio/{audio_id}")
async def websocket_audio_stream(websocket: WebSocket, audio_id: str):
    """
    오디오 스트림 WebSocket

    Args:
        websocket: WebSocket 연결
        audio_id: 오디오 ID
    """
    client_id = f"audio_{audio_id}_{int(time.time())}"

    await manager.connect(websocket, client_id)

    try:
        # 오디오 확인
        if audio_id not in audio_storage:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason=f"오디오를 찾을 수 없습니다: {audio_id}",
            )
            return

        audio_info = audio_storage[audio_id]
        audio_format = AudioFormat.from_extension(Path(audio_info.filename).suffix)
        file_path = UPLOAD_DIR / f"{audio_id}.{audio_format.value}"

        if not file_path.exists():
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="파일을 찾을 수 없습니다",
            )
            return

        # 오디오 로드
        import librosa

        y, sr = librosa.load(str(file_path), sr=None)

        # 버퍼 크기 (기본값: 2048)
        buffer_size = config.get("audio.buffer_size", 2048)

        # 프레임 단위로 전송
        num_frames = len(y) // buffer_size
        frame_index = 0

        logger.info(f"오디오 스트림 시작: {audio_id} ({num_frames} frames)")

        while frame_index < num_frames:
            # 버퍼 데이터
            start_idx = frame_index * buffer_size
            end_idx = start_idx + buffer_size
            audio_buffer = y[start_idx:end_idx]

            # 메시지 생성
            stream_data = AudioStreamData(
                frame_index=frame_index,
                audio_data=audio_buffer.tolist(),
                sample_rate=sr,
            )

            message = StreamMessage(
                type="audio",
                timestamp=time.time(),
                data=stream_data.model_dump(),
            )

            # 전송
            await manager.send_message(message, client_id)

            # 프레임 레이트 조절 (실시간 재생)
            frame_duration = buffer_size / sr
            await asyncio.sleep(frame_duration)

            frame_index += 1

        # 종료 메시지
        end_message = StreamMessage(
            type="audio_end",
            timestamp=time.time(),
            data={"total_frames": num_frames},
        )

        await manager.send_message(end_message, client_id)

        logger.info(f"오디오 스트림 완료: {audio_id}")

    except WebSocketDisconnect:
        logger.info(f"클라이언트 연결 해제: {client_id}")
    except Exception as e:
        logger.error(f"오디오 스트림 에러: {e}", exc_info=True)
    finally:
        manager.disconnect(client_id)


@router.websocket("/ws/features/{audio_id}")
async def websocket_feature_stream(websocket: WebSocket, audio_id: str):
    """
    특성 스트림 WebSocket

    Args:
        websocket: WebSocket 연결
        audio_id: 오디오 ID
    """
    client_id = f"features_{audio_id}_{int(time.time())}"

    await manager.connect(websocket, client_id)

    try:
        # 오디오 확인
        if audio_id not in audio_storage:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason=f"오디오를 찾을 수 없습니다: {audio_id}",
            )
            return

        audio_info = audio_storage[audio_id]
        audio_format = AudioFormat.from_extension(Path(audio_info.filename).suffix)
        file_path = UPLOAD_DIR / f"{audio_id}.{audio_format.value}"

        if not file_path.exists():
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="파일을 찾을 수 없습니다",
            )
            return

        # 분석 수행
        logger.info(f"특성 분석 시작: {audio_id}")

        extractor = FeatureExtractor()
        result = extractor.extract(file_path)

        # 특성 추출
        rms_energy = result.timbre.get("rms_energy")
        spectral_centroid = result.spectral.get("spectral_centroid")
        tempo = result.rhythm.get("tempo", 120.0)

        # 프레임 수
        num_frames = len(rms_energy) if rms_energy is not None else 0

        if num_frames == 0:
            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason="특성 추출 실패",
            )
            return

        logger.info(f"특성 스트림 시작: {audio_id} ({num_frames} frames)")

        # 프레임 단위로 전송
        frame_duration = config.get("analysis.hop_size", 512) / config.get(
            "audio.sample_rate", 44100
        )

        for frame_index in range(num_frames):
            # 특성 데이터
            energy = float(rms_energy[frame_index]) if rms_energy is not None else None
            centroid = (
                float(spectral_centroid[frame_index])
                if spectral_centroid is not None and frame_index < len(spectral_centroid)
                else None
            )

            stream_data = FeatureStreamData(
                frame_index=frame_index,
                tempo=float(tempo),
                energy=energy,
                spectral_centroid=centroid,
                pitch=None,  # TODO: pitch 추가
            )

            message = StreamMessage(
                type="features",
                timestamp=time.time(),
                data=stream_data.model_dump(),
            )

            # 전송
            await manager.send_message(message, client_id)

            # 프레임 레이트 조절
            await asyncio.sleep(frame_duration)

        # 종료 메시지
        end_message = StreamMessage(
            type="features_end",
            timestamp=time.time(),
            data={"total_frames": num_frames},
        )

        await manager.send_message(end_message, client_id)

        logger.info(f"특성 스트림 완료: {audio_id}")

    except WebSocketDisconnect:
        logger.info(f"클라이언트 연결 해제: {client_id}")
    except Exception as e:
        logger.error(f"특성 스트림 에러: {e}", exc_info=True)
    finally:
        manager.disconnect(client_id)


@router.websocket("/ws/visualization/{audio_id}")
async def websocket_visualization_stream(
    websocket: WebSocket,
    audio_id: str,
    viz_type: str = "particles",
):
    """
    시각화 데이터 스트림 WebSocket

    Args:
        websocket: WebSocket 연결
        audio_id: 오디오 ID
        viz_type: 시각화 타입
    """
    client_id = f"viz_{audio_id}_{int(time.time())}"

    await manager.connect(websocket, client_id)

    try:
        # 오디오 확인
        if audio_id not in audio_storage:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason=f"오디오를 찾을 수 없습니다: {audio_id}",
            )
            return

        audio_info = audio_storage[audio_id]
        audio_format = AudioFormat.from_extension(Path(audio_info.filename).suffix)
        file_path = UPLOAD_DIR / f"{audio_id}.{audio_format.value}"

        if not file_path.exists():
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="파일을 찾을 수 없습니다",
            )
            return

        # 분석 수행
        logger.info(f"시각화 데이터 분석 시작: {audio_id}")

        extractor = FeatureExtractor()
        result = extractor.extract(file_path)

        # 시각화 타입 변환
        try:
            viz_type_enum = VisualizationType(viz_type)
        except ValueError:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason=f"지원하지 않는 시각화 타입: {viz_type}",
            )
            return

        # 특성 추출
        rms_energy = result.timbre.get("rms_energy")
        spectral_centroid = result.spectral.get("spectral_centroid")
        num_frames = len(rms_energy) if rms_energy is not None else 0

        logger.info(f"시각화 스트림 시작: {audio_id} ({num_frames} frames)")

        # 프레임 단위로 전송
        frame_duration = config.get("analysis.hop_size", 512) / config.get(
            "audio.sample_rate", 44100
        )

        for frame_index in range(num_frames):
            # 시각화 데이터 생성
            viz_data = {
                "energy": float(rms_energy[frame_index]) if rms_energy is not None else 0.0,
                "centroid": (
                    float(spectral_centroid[frame_index])
                    if spectral_centroid is not None and frame_index < len(spectral_centroid)
                    else 0.0
                ),
            }

            stream_data = VisualizationStreamData(
                frame_index=frame_index,
                viz_type=viz_type_enum,
                data=viz_data,
            )

            message = StreamMessage(
                type="visualization",
                timestamp=time.time(),
                data=stream_data.model_dump(),
            )

            # 전송
            await manager.send_message(message, client_id)

            # 프레임 레이트 조절
            await asyncio.sleep(frame_duration)

        # 종료 메시지
        end_message = StreamMessage(
            type="visualization_end",
            timestamp=time.time(),
            data={"total_frames": num_frames},
        )

        await manager.send_message(end_message, client_id)

        logger.info(f"시각화 스트림 완료: {audio_id}")

    except WebSocketDisconnect:
        logger.info(f"클라이언트 연결 해제: {client_id}")
    except Exception as e:
        logger.error(f"시각화 스트림 에러: {e}", exc_info=True)
    finally:
        manager.disconnect(client_id)
