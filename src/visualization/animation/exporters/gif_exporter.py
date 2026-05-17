"""
GIF 내보내기

애니메이션을 GIF 형식으로 내보내기
"""

import io
from pathlib import Path

import numpy as np

from src.utils.logging import get_logger

logger = get_logger(__name__)


class GIFExporter:
    """
    GIF 내보내기

    프레임 시퀀스를 GIF 애니메이션으로 변환
    """

    def __init__(self, config: dict = None):
        """
        GIFExporter 초기화

        Args:
            config: 설정 딕셔너리
        """
        self.config = config or {}
        self.default_fps = self.config.get("fps", 30)
        self.loop = self.config.get("loop", 0)  # 0 = 무한 반복
        self.optimize = self.config.get("optimize", True)
        self.quality = self.config.get("quality", 85)

    def export(
        self,
        frames: list[np.ndarray],
        output_path: str | Path,
        fps: int = None,
        loop: int = None,
        optimize: bool = None,
        **kwargs
    ) -> str:
        """
        프레임을 GIF로 내보내기

        Args:
            frames: 프레임 이미지 배열 리스트
            output_path: 출력 파일 경로
            fps: 프레임 레이트
            loop: 반복 횟수 (0 = 무한)
            optimize: 최적화 여부
            **kwargs: 추가 옵션

        Returns:
            출력 파일 경로
        """
        if not frames:
            raise ValueError("내보낼 프레임이 없음")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fps = fps or self.default_fps
        loop = loop if loop is not None else self.loop
        optimize = optimize if optimize is not None else self.optimize

        duration = int(1000 / fps)  # 밀리초 단위

        logger.info(f"GIF 내보내기 시작: {len(frames)}프레임, {fps}fps")

        try:
            import imageio

            # imageio로 GIF 생성
            with imageio.get_writer(
                str(output_path),
                mode='I',
                duration=duration / 1000,  # 초 단위
                loop=loop,
            ) as writer:
                for i, frame in enumerate(frames):
                    # uint8로 변환
                    if frame.dtype != np.uint8:
                        frame = np.clip(frame, 0, 255).astype(np.uint8)

                    writer.append_data(frame)

                    if (i + 1) % 10 == 0:
                        logger.debug(f"프레임 {i + 1}/{len(frames)} 저장 중")

            logger.info(f"GIF 내보내기 완료: {output_path}")
            return str(output_path)

        except ImportError:
            logger.warning("imageio를 찾을 수 없음, PIL 사용")
            return self._export_with_pil(frames, output_path, duration, loop, optimize)

    def _export_with_pil(
        self,
        frames: list[np.ndarray],
        output_path: Path,
        duration: int,
        loop: int,
        optimize: bool
    ) -> str:
        """
        PIL을 사용한 GIF 내보내기

        Args:
            frames: 프레임 리스트
            output_path: 출력 경로
            duration: 프레임 간격 (밀리초)
            loop: 반복 횟수
            optimize: 최적화 여부

        Returns:
            출력 파일 경로
        """
        from PIL import Image

        pil_frames = []

        for frame in frames:
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)

            img = Image.fromarray(frame)

            # 팔레트 모드로 변환 (GIF 용량 감소)
            if optimize:
                img = img.convert('P', palette=Image.ADAPTIVE, colors=256)

            pil_frames.append(img)

        # 첫 프레임에 나머지 프레임 추가
        pil_frames[0].save(
            output_path,
            save_all=True,
            append_images=pil_frames[1:],
            duration=duration,
            loop=loop,
            optimize=optimize,
        )

        logger.info(f"GIF 내보내기 완료 (PIL): {output_path}")
        return str(output_path)

    def export_to_bytes(
        self,
        frames: list[np.ndarray],
        fps: int = None,
        **kwargs
    ) -> bytes:
        """
        프레임을 GIF 바이트로 변환

        Args:
            frames: 프레임 리스트
            fps: 프레임 레이트
            **kwargs: 추가 옵션

        Returns:
            GIF 바이트
        """
        from PIL import Image

        fps = fps or self.default_fps
        duration = int(1000 / fps)

        pil_frames = []
        for frame in frames:
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            pil_frames.append(Image.fromarray(frame))

        buf = io.BytesIO()
        pil_frames[0].save(
            buf,
            format='GIF',
            save_all=True,
            append_images=pil_frames[1:],
            duration=duration,
            loop=self.loop,
        )

        return buf.getvalue()

    def create_thumbnail(
        self,
        frames: list[np.ndarray],
        output_path: str | Path,
        frame_index: int = 0,
        size: tuple = (200, 200)
    ) -> str:
        """
        썸네일 이미지 생성

        Args:
            frames: 프레임 리스트
            output_path: 출력 경로
            frame_index: 사용할 프레임 인덱스
            size: 썸네일 크기

        Returns:
            출력 파일 경로
        """
        from PIL import Image

        frame = frames[frame_index % len(frames)]
        if frame.dtype != np.uint8:
            frame = np.clip(frame, 0, 255).astype(np.uint8)

        img = Image.fromarray(frame)
        img.thumbnail(size, Image.Resampling.LANCZOS)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)

        logger.info(f"썸네일 생성 완료: {output_path}")
        return str(output_path)
