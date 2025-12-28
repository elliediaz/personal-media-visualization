"""
애니메이션 엔진

시각화 애니메이션 생성을 위한 핵심 엔진
"""

import numpy as np
from pathlib import Path
from typing import List, Callable, Any
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor
import io

from src.analysis.result import AnalysisResult
from src.visualization.base import BaseVisualizer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AnimationEngine:
    """
    애니메이션 엔진

    시각화 프레임 생성 및 관리
    """

    def __init__(self, config: dict = None):
        """
        AnimationEngine 초기화

        Args:
            config: 설정 딕셔너리
        """
        self.config = config or {}
        self.fps = self.config.get("fps", 30)
        self.duration = self.config.get("duration", 10.0)
        self.width = self.config.get("width", 800)
        self.height = self.config.get("height", 600)

        self.frames = []
        self.frame_count = 0

    def generate_frames(
        self,
        visualizer: BaseVisualizer,
        result: AnalysisResult,
        duration: float = None,
        fps: int = None,
        progress_callback: Callable[[int, int], None] = None,
        **kwargs
    ) -> List[np.ndarray]:
        """
        애니메이션 프레임 생성

        Args:
            visualizer: 시각화 객체
            result: 분석 결과
            duration: 애니메이션 길이 (초)
            fps: 프레임 레이트
            progress_callback: 진행 콜백 함수
            **kwargs: 시각화 옵션

        Returns:
            프레임 이미지 배열 리스트
        """
        duration = duration or self.duration
        fps = fps or self.fps
        total_frames = int(duration * fps)

        self.frames = []
        self.frame_count = total_frames

        logger.info(f"프레임 생성 시작: {total_frames}프레임, {fps}fps, {duration}초")

        for frame_idx in range(total_frames):
            # 시각화 렌더링
            if hasattr(visualizer, 'render_animation_frame'):
                fig = visualizer.render_animation_frame(
                    result,
                    frame_index=frame_idx,
                    total_frames=total_frames,
                    **kwargs
                )
            else:
                # 기본 렌더링 (time 파라미터 사용)
                time = (frame_idx / total_frames) * np.pi * 4
                fig = visualizer.render(result, time=time, **kwargs)

            # Figure를 이미지로 변환
            frame = self._figure_to_array(fig)
            self.frames.append(frame)

            # Figure 정리
            plt.close(fig)

            # 진행 콜백
            if progress_callback:
                progress_callback(frame_idx + 1, total_frames)

            if (frame_idx + 1) % 10 == 0:
                logger.debug(f"프레임 {frame_idx + 1}/{total_frames} 생성 완료")

        logger.info(f"프레임 생성 완료: {len(self.frames)}프레임")
        return self.frames

    def generate_frames_parallel(
        self,
        visualizer_class: type,
        result: AnalysisResult,
        duration: float = None,
        fps: int = None,
        max_workers: int = 4,
        progress_callback: Callable[[int, int], None] = None,
        **kwargs
    ) -> List[np.ndarray]:
        """
        병렬 프레임 생성

        Args:
            visualizer_class: 시각화 클래스
            result: 분석 결과
            duration: 애니메이션 길이 (초)
            fps: 프레임 레이트
            max_workers: 최대 워커 수
            progress_callback: 진행 콜백 함수
            **kwargs: 시각화 옵션

        Returns:
            프레임 이미지 배열 리스트
        """
        duration = duration or self.duration
        fps = fps or self.fps
        total_frames = int(duration * fps)

        logger.info(f"병렬 프레임 생성 시작: {total_frames}프레임, {max_workers} 워커")

        def render_frame(frame_idx):
            visualizer = visualizer_class()
            if hasattr(visualizer, 'render_animation_frame'):
                fig = visualizer.render_animation_frame(
                    result,
                    frame_index=frame_idx,
                    total_frames=total_frames,
                    **kwargs
                )
            else:
                time = (frame_idx / total_frames) * np.pi * 4
                fig = visualizer.render(result, time=time, **kwargs)

            frame = self._figure_to_array(fig)
            plt.close(fig)
            return frame_idx, frame

        frames_dict = {}
        completed = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(render_frame, i) for i in range(total_frames)]

            for future in futures:
                frame_idx, frame = future.result()
                frames_dict[frame_idx] = frame
                completed += 1

                if progress_callback:
                    progress_callback(completed, total_frames)

        # 순서대로 정렬
        self.frames = [frames_dict[i] for i in range(total_frames)]
        self.frame_count = total_frames

        logger.info(f"병렬 프레임 생성 완료: {len(self.frames)}프레임")
        return self.frames

    def _figure_to_array(self, fig) -> np.ndarray:
        """
        matplotlib Figure를 numpy 배열로 변환

        Args:
            fig: matplotlib Figure

        Returns:
            RGB 이미지 배열
        """
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format='png',
            facecolor=fig.get_facecolor(),
            dpi=100,
            bbox_inches='tight',
            pad_inches=0.1
        )
        buf.seek(0)

        from PIL import Image
        image = Image.open(buf)
        array = np.array(image)

        # RGBA -> RGB 변환
        if array.shape[-1] == 4:
            array = array[:, :, :3]

        return array

    def apply_post_processing(
        self,
        frames: List[np.ndarray] = None,
        effects: List[str] = None
    ) -> List[np.ndarray]:
        """
        프레임에 후처리 효과 적용

        Args:
            frames: 프레임 리스트 (None이면 self.frames 사용)
            effects: 적용할 효과 리스트

        Returns:
            후처리된 프레임 리스트
        """
        frames = frames or self.frames
        effects = effects or []

        if not frames:
            logger.warning("후처리할 프레임이 없음")
            return frames

        logger.info(f"후처리 시작: {len(effects)}개 효과")

        from src.visualization.retro.crt_processor import CRTProcessor

        processed_frames = []

        for i, frame in enumerate(frames):
            processed = frame.copy()

            for effect in effects:
                if effect == "crt":
                    processor = CRTProcessor()
                    processed = processor.process(processed)
                elif effect == "scanlines":
                    from src.visualization.retro.effects.scanlines import ScanlineEffect
                    scanline = ScanlineEffect()
                    processed = scanline.apply(processed)
                elif effect == "vignette":
                    from src.visualization.retro.effects.vignette import VignetteEffect
                    vignette = VignetteEffect()
                    processed = vignette.apply(processed)

            processed_frames.append(processed)

        logger.info(f"후처리 완료: {len(processed_frames)}프레임")
        return processed_frames

    def get_frame(self, index: int) -> np.ndarray:
        """
        특정 프레임 가져오기

        Args:
            index: 프레임 인덱스

        Returns:
            프레임 이미지 배열
        """
        if not self.frames:
            raise ValueError("프레임이 생성되지 않음")
        return self.frames[index % len(self.frames)]

    def clear(self):
        """프레임 메모리 정리"""
        self.frames = []
        self.frame_count = 0


class AnimationBuilder:
    """
    애니메이션 빌더

    편리한 애니메이션 생성을 위한 빌더 패턴
    """

    def __init__(self):
        """AnimationBuilder 초기화"""
        self._visualizer = None
        self._result = None
        self._duration = 10.0
        self._fps = 30
        self._effects = []
        self._output_path = None
        self._format = "gif"

    def with_visualizer(self, visualizer: BaseVisualizer) -> 'AnimationBuilder':
        """
        시각화 설정

        Args:
            visualizer: 시각화 객체

        Returns:
            self
        """
        self._visualizer = visualizer
        return self

    def with_result(self, result: AnalysisResult) -> 'AnimationBuilder':
        """
        분석 결과 설정

        Args:
            result: 분석 결과

        Returns:
            self
        """
        self._result = result
        return self

    def with_duration(self, seconds: float) -> 'AnimationBuilder':
        """
        애니메이션 길이 설정

        Args:
            seconds: 길이 (초)

        Returns:
            self
        """
        self._duration = seconds
        return self

    def with_fps(self, fps: int) -> 'AnimationBuilder':
        """
        프레임 레이트 설정

        Args:
            fps: FPS

        Returns:
            self
        """
        self._fps = fps
        return self

    def with_effect(self, effect: str) -> 'AnimationBuilder':
        """
        후처리 효과 추가

        Args:
            effect: 효과 이름

        Returns:
            self
        """
        self._effects.append(effect)
        return self

    def with_output(self, path: str, format: str = "gif") -> 'AnimationBuilder':
        """
        출력 설정

        Args:
            path: 출력 경로
            format: 출력 형식 (gif, mp4)

        Returns:
            self
        """
        self._output_path = path
        self._format = format
        return self

    def build(self, progress_callback: Callable = None) -> str:
        """
        애니메이션 생성 및 내보내기

        Args:
            progress_callback: 진행 콜백

        Returns:
            출력 파일 경로
        """
        if not self._visualizer or not self._result:
            raise ValueError("시각화와 분석 결과가 필요함")

        # 프레임 생성
        engine = AnimationEngine({
            "fps": self._fps,
            "duration": self._duration,
        })

        frames = engine.generate_frames(
            self._visualizer,
            self._result,
            progress_callback=progress_callback
        )

        # 후처리 적용
        if self._effects:
            frames = engine.apply_post_processing(frames, self._effects)

        # 내보내기
        if self._output_path:
            if self._format == "gif":
                from src.visualization.animation.exporters.gif_exporter import GIFExporter
                exporter = GIFExporter()
                return exporter.export(frames, self._output_path, fps=self._fps)
            elif self._format == "mp4":
                from src.visualization.animation.exporters.mp4_exporter import MP4Exporter
                exporter = MP4Exporter()
                return exporter.export(frames, self._output_path, fps=self._fps)

        return None
