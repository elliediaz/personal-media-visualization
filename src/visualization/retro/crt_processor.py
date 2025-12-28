"""
CRT 후처리 프로세서

여러 CRT 효과를 파이프라인으로 연결하여 적용합니다.
"""

from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from src.core.config import config
from src.utils.logging import get_logger

from .effects.base_effect import BaseEffect
from .effects.scanlines import ScanlinesEffect
from .effects.chromatic import ChromaticAberrationEffect
from .effects.noise import NoiseEffect, GlitchEffect
from .effects.bloom import BloomEffect, HDRBloomEffect
from .effects.vignette import VignetteEffect, CurvatureEffect

logger = get_logger(__name__)


class CRTProcessor:
    """
    CRT 효과 파이프라인 프로세서

    여러 효과를 순서대로 적용합니다.
    """

    def __init__(self, config_override: dict = None):
        """
        CRT 프로세서 초기화

        Args:
            config_override: 설정 오버라이드
        """
        self.effects: list[BaseEffect] = []
        self._load_config(config_override)

    def _load_config(self, config_override: dict = None) -> None:
        """
        설정에서 효과 파라미터 로드

        Args:
            config_override: 설정 오버라이드
        """
        cfg = config_override or {}
        viz_config = config.get("visualization", {})
        crt_config = viz_config.get("crt", {})

        # 설정 병합
        crt_config.update(cfg)

        if not crt_config.get("enabled", True):
            return

        # 효과 순서: 곡률 -> 스캔라인 -> 색수차 -> 블룸 -> 노이즈 -> 비네트
        self._add_curvature(crt_config.get("curvature", {}))
        self._add_scanlines(crt_config.get("scanlines", {}))
        self._add_chromatic(crt_config.get("chromatic_aberration", {}))
        self._add_bloom(crt_config.get("bloom", {}))
        self._add_noise(crt_config.get("noise", {}))
        self._add_vignette(crt_config.get("vignette", {}))

    def _add_curvature(self, cfg: dict) -> None:
        """곡률 효과 추가"""
        if cfg.get("enabled", False):
            self.effects.append(
                CurvatureEffect(
                    enabled=True,
                    intensity=cfg.get("intensity", 1.0),
                    curvature=cfg.get("amount", 0.03),
                )
            )

    def _add_scanlines(self, cfg: dict) -> None:
        """스캔라인 효과 추가"""
        if cfg.get("enabled", True):
            self.effects.append(
                ScanlinesEffect(
                    enabled=True,
                    intensity=cfg.get("intensity", 0.3),
                    line_width=cfg.get("line_width", 2),
                    gap=cfg.get("gap", 2),
                    animated=cfg.get("animated", False),
                )
            )

    def _add_chromatic(self, cfg: dict) -> None:
        """색수차 효과 추가"""
        if cfg.get("enabled", True):
            self.effects.append(
                ChromaticAberrationEffect(
                    enabled=True,
                    intensity=cfg.get("intensity", 1.0),
                    offset=cfg.get("offset", 2),
                    radial=cfg.get("radial", True),
                )
            )

    def _add_bloom(self, cfg: dict) -> None:
        """블룸 효과 추가"""
        if cfg.get("enabled", True):
            use_hdr = cfg.get("hdr", False)
            if use_hdr:
                self.effects.append(
                    HDRBloomEffect(
                        enabled=True,
                        intensity=cfg.get("intensity", 0.4),
                        levels=cfg.get("levels", 4),
                        base_radius=cfg.get("radius", 5),
                        threshold=cfg.get("threshold", 0.6),
                    )
                )
            else:
                self.effects.append(
                    BloomEffect(
                        enabled=True,
                        intensity=cfg.get("intensity", 0.4),
                        radius=cfg.get("radius", 5),
                        threshold=cfg.get("threshold", 0.6),
                    )
                )

    def _add_noise(self, cfg: dict) -> None:
        """노이즈 효과 추가"""
        if cfg.get("enabled", True):
            self.effects.append(
                NoiseEffect(
                    enabled=True,
                    intensity=cfg.get("intensity", 0.05),
                    monochrome=cfg.get("monochrome", True),
                    animated=cfg.get("animated", True),
                )
            )

    def _add_vignette(self, cfg: dict) -> None:
        """비네트 효과 추가"""
        if cfg.get("enabled", True):
            self.effects.append(
                VignetteEffect(
                    enabled=True,
                    intensity=cfg.get("intensity", 0.6),
                    radius=cfg.get("radius", 0.8),
                    softness=cfg.get("softness", 0.5),
                )
            )

    def add_effect(self, effect: BaseEffect) -> "CRTProcessor":
        """
        효과 추가

        Args:
            effect: 추가할 효과

        Returns:
            self (체이닝 지원)
        """
        self.effects.append(effect)
        return self

    def remove_effect(self, effect_type: type) -> bool:
        """
        특정 타입의 효과 제거

        Args:
            effect_type: 제거할 효과 타입

        Returns:
            제거 성공 여부
        """
        for i, effect in enumerate(self.effects):
            if isinstance(effect, effect_type):
                self.effects.pop(i)
                return True
        return False

    def clear_effects(self) -> None:
        """모든 효과 제거"""
        self.effects.clear()

    def process(self, image: np.ndarray) -> np.ndarray:
        """
        이미지에 모든 효과 적용

        Args:
            image: 입력 이미지 (H, W, C), uint8 또는 float

        Returns:
            효과가 적용된 이미지
        """
        result = image.copy()
        for effect in self.effects:
            if effect.enabled:
                result = effect.apply(result)
                logger.debug(f"효과 적용: {effect.__class__.__name__}")
        return result

    def process_file(
        self,
        input_path: Path | str,
        output_path: Optional[Path | str] = None,
    ) -> np.ndarray:
        """
        파일에서 이미지 로드 후 효과 적용

        Args:
            input_path: 입력 이미지 경로
            output_path: 출력 이미지 경로 (None이면 저장 안 함)

        Returns:
            효과가 적용된 이미지
        """
        input_path = Path(input_path)

        # 이미지 로드
        img = Image.open(input_path)
        image = np.array(img.convert("RGB"))

        # 효과 적용
        result = self.process(image)

        # 저장
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(result).save(output_path)
            logger.info(f"CRT 효과 적용 완료: {output_path}")

        return result

    def update_animation(self, delta: float = 0.02) -> None:
        """
        애니메이션 상태 업데이트

        Args:
            delta: 시간 변화량
        """
        for effect in self.effects:
            if hasattr(effect, "update_phase"):
                effect.update_phase(delta)

    def get_effect(self, effect_type: type) -> Optional[BaseEffect]:
        """
        특정 타입의 효과 가져오기

        Args:
            effect_type: 효과 타입

        Returns:
            효과 인스턴스 또는 None
        """
        for effect in self.effects:
            if isinstance(effect, effect_type):
                return effect
        return None

    def __repr__(self) -> str:
        effect_names = [e.__class__.__name__ for e in self.effects]
        return f"CRTProcessor(effects={effect_names})"


def create_default_processor() -> CRTProcessor:
    """
    기본 CRT 프로세서 생성

    Returns:
        기본 설정의 CRT 프로세서
    """
    processor = CRTProcessor()

    # 기본 효과가 없으면 추가
    if not processor.effects:
        processor.add_effect(ScanlinesEffect(intensity=0.25))
        processor.add_effect(ChromaticAberrationEffect(offset=2))
        processor.add_effect(BloomEffect(intensity=0.3, threshold=0.7))
        processor.add_effect(NoiseEffect(intensity=0.03))
        processor.add_effect(VignetteEffect(intensity=0.5))

    return processor


def create_minimal_processor() -> CRTProcessor:
    """
    최소 CRT 프로세서 생성 (성능 우선)

    Returns:
        최소 설정의 CRT 프로세서
    """
    processor = CRTProcessor()
    processor.clear_effects()

    processor.add_effect(ScanlinesEffect(intensity=0.2, line_width=1, gap=1))
    processor.add_effect(VignetteEffect(intensity=0.4))

    return processor


def create_full_processor() -> CRTProcessor:
    """
    풀 CRT 프로세서 생성 (모든 효과 활성화)

    Returns:
        풀 설정의 CRT 프로세서
    """
    processor = CRTProcessor()
    processor.clear_effects()

    processor.add_effect(CurvatureEffect(curvature=0.02))
    processor.add_effect(ScanlinesEffect(intensity=0.3, animated=True))
    processor.add_effect(ChromaticAberrationEffect(offset=3, radial=True))
    processor.add_effect(HDRBloomEffect(intensity=0.5, levels=4))
    processor.add_effect(NoiseEffect(intensity=0.05))
    processor.add_effect(GlitchEffect(frequency=0.05, intensity=0.3))
    processor.add_effect(VignetteEffect(intensity=0.6))

    return processor
