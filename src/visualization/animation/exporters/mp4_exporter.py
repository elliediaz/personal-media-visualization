"""
MP4 내보내기

애니메이션을 MP4 형식으로 내보내기
"""

import subprocess
import tempfile
from pathlib import Path

import numpy as np

from src.utils.logging import get_logger

logger = get_logger(__name__)


class MP4Exporter:
    """
    MP4 내보내기

    프레임 시퀀스를 MP4 비디오로 변환
    """

    def __init__(self, config: dict = None):
        """
        MP4Exporter 초기화

        Args:
            config: 설정 딕셔너리
        """
        self.config = config or {}
        self.default_fps = self.config.get("fps", 30)
        self.codec = self.config.get("codec", "libx264")
        self.quality = self.config.get("quality", 23)  # CRF 값 (낮을수록 고품질)
        self.pixel_format = self.config.get("pixel_format", "yuv420p")
        self.audio_path = self.config.get("audio_path", None)

    def export(
        self,
        frames: list[np.ndarray],
        output_path: str | Path,
        fps: int = None,
        codec: str = None,
        quality: int = None,
        audio_path: str = None,
        **kwargs
    ) -> str:
        """
        프레임을 MP4로 내보내기

        Args:
            frames: 프레임 이미지 배열 리스트
            output_path: 출력 파일 경로
            fps: 프레임 레이트
            codec: 비디오 코덱
            quality: 품질 (CRF)
            audio_path: 오디오 파일 경로 (옵션)
            **kwargs: 추가 옵션

        Returns:
            출력 파일 경로
        """
        if not frames:
            raise ValueError("내보낼 프레임이 없음")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fps = fps or self.default_fps
        codec = codec or self.codec
        quality = quality if quality is not None else self.quality
        audio_path = audio_path or self.audio_path

        logger.info(f"MP4 내보내기 시작: {len(frames)}프레임, {fps}fps")

        try:
            return self._export_with_imageio(
                frames, output_path, fps, codec, quality, audio_path
            )
        except ImportError:
            logger.warning("imageio-ffmpeg를 찾을 수 없음, ffmpeg 직접 사용")
            return self._export_with_ffmpeg(
                frames, output_path, fps, codec, quality, audio_path
            )

    def _export_with_imageio(
        self,
        frames: list[np.ndarray],
        output_path: Path,
        fps: int,
        codec: str,
        quality: int,
        audio_path: str
    ) -> str:
        """
        imageio-ffmpeg를 사용한 MP4 내보내기

        Args:
            frames: 프레임 리스트
            output_path: 출력 경로
            fps: FPS
            codec: 코덱
            quality: 품질
            audio_path: 오디오 경로

        Returns:
            출력 파일 경로
        """
        import imageio

        # 오디오 없이 먼저 저장
        temp_path = output_path if not audio_path else output_path.with_suffix('.temp.mp4')

        with imageio.get_writer(
            str(temp_path),
            fps=fps,
            codec=codec,
            quality=quality,
            pixelformat=self.pixel_format,
            macro_block_size=8,
        ) as writer:
            for i, frame in enumerate(frames):
                if frame.dtype != np.uint8:
                    frame = np.clip(frame, 0, 255).astype(np.uint8)

                writer.append_data(frame)

                if (i + 1) % 10 == 0:
                    logger.debug(f"프레임 {i + 1}/{len(frames)} 인코딩 중")

        # 오디오 추가
        if audio_path and Path(audio_path).exists():
            self._add_audio(temp_path, audio_path, output_path, fps, len(frames))
            temp_path.unlink()  # 임시 파일 삭제
        elif audio_path:
            logger.warning(f"오디오 파일을 찾을 수 없음: {audio_path}")

        logger.info(f"MP4 내보내기 완료: {output_path}")
        return str(output_path)

    def _export_with_ffmpeg(
        self,
        frames: list[np.ndarray],
        output_path: Path,
        fps: int,
        codec: str,
        quality: int,
        audio_path: str
    ) -> str:
        """
        ffmpeg를 직접 사용한 MP4 내보내기

        Args:
            frames: 프레임 리스트
            output_path: 출력 경로
            fps: FPS
            codec: 코덱
            quality: 품질
            audio_path: 오디오 경로

        Returns:
            출력 파일 경로
        """
        from PIL import Image

        # 임시 디렉토리에 프레임 저장
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)

            # 프레임 저장
            for i, frame in enumerate(frames):
                if frame.dtype != np.uint8:
                    frame = np.clip(frame, 0, 255).astype(np.uint8)

                img = Image.fromarray(frame)
                img.save(temp_dir / f"frame_{i:05d}.png")

            # ffmpeg 명령 구성
            cmd = [
                'ffmpeg', '-y',
                '-framerate', str(fps),
                '-i', str(temp_dir / 'frame_%05d.png'),
            ]

            if audio_path and Path(audio_path).exists():
                cmd.extend(['-i', audio_path])
                cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
                cmd.extend(['-shortest'])

            cmd.extend([
                '-c:v', codec,
                '-crf', str(quality),
                '-pix_fmt', self.pixel_format,
                str(output_path)
            ])

            # ffmpeg 실행
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"ffmpeg 오류: {result.stderr}")
                raise RuntimeError(f"ffmpeg 실패: {result.stderr}")

        logger.info(f"MP4 내보내기 완료 (ffmpeg): {output_path}")
        return str(output_path)

    def _add_audio(
        self,
        video_path: Path,
        audio_path: str,
        output_path: Path,
        fps: int,
        frame_count: int
    ):
        """
        비디오에 오디오 추가

        Args:
            video_path: 비디오 파일 경로
            audio_path: 오디오 파일 경로
            output_path: 출력 경로
            fps: FPS
            frame_count: 프레임 수
        """
        duration = frame_count / fps

        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-t', str(duration),
            '-shortest',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.warning(f"오디오 추가 실패: {result.stderr}")
            # 오디오 없이 복사
            import shutil
            shutil.copy(video_path, output_path)

    def export_with_audio(
        self,
        frames: list[np.ndarray],
        audio_path: str,
        output_path: str | Path,
        fps: int = None,
        **kwargs
    ) -> str:
        """
        오디오와 함께 MP4 내보내기

        Args:
            frames: 프레임 리스트
            audio_path: 오디오 파일 경로
            output_path: 출력 경로
            fps: FPS
            **kwargs: 추가 옵션

        Returns:
            출력 파일 경로
        """
        return self.export(frames, output_path, fps, audio_path=audio_path, **kwargs)

    def create_preview(
        self,
        frames: list[np.ndarray],
        output_path: str | Path,
        fps: int = None,
        duration: float = 5.0
    ) -> str:
        """
        미리보기 비디오 생성 (짧은 버전)

        Args:
            frames: 프레임 리스트
            output_path: 출력 경로
            fps: FPS
            duration: 미리보기 길이 (초)

        Returns:
            출력 파일 경로
        """
        fps = fps or self.default_fps
        preview_frames = int(duration * fps)

        # 프레임 서브샘플링
        if len(frames) > preview_frames:
            indices = np.linspace(0, len(frames) - 1, preview_frames).astype(int)
            preview = [frames[i] for i in indices]
        else:
            preview = frames

        return self.export(
            preview,
            output_path,
            fps=fps,
            quality=28  # 낮은 품질로 빠른 인코딩
        )
