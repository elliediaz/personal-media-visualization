"""
시각화 기본 클래스

모든 시각화 클래스의 기반이 되는 추상 클래스입니다.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import matplotlib.pyplot as plt
import numpy as np

from src.core.config import config
from src.utils.logging import get_logger

if TYPE_CHECKING:
    from src.visualization.retro import CRTProcessor

logger = get_logger(__name__)


class BaseVisualizer(ABC):
    """
    시각화 기본 추상 클래스

    모든 시각화 클래스가 상속해야 하는 기본 클래스입니다.
    """

    def __init__(self, config_override: dict = None):
        """
        BaseVisualizer 초기화

        Args:
            config_override: 설정 오버라이드
        """
        cfg = config_override or {}

        # 시각화 설정
        viz_config = config.get("visualization", {})
        general_config = viz_config.get("general", {})

        self.width = cfg.get("width", general_config.get("width", 1920))
        self.height = cfg.get("height", general_config.get("height", 1080))
        self.dpi = cfg.get("dpi", general_config.get("dpi", 100))
        self.fps = cfg.get("fps", general_config.get("fps", 60))

        # 색상 설정
        colors_config = viz_config.get("colors", {})
        self.bg_color = cfg.get("bg_color", colors_config.get("background", "#000000"))
        self.fg_color = cfg.get("fg_color", colors_config.get("foreground", "#FFFFFF"))
        self.primary_color = cfg.get("primary_color", colors_config.get("primary", "#00FFFF"))
        self.secondary_color = cfg.get(
            "secondary_color", colors_config.get("secondary", "#FF00FF")
        )

        # Figure 초기화
        self.fig = None
        self.ax = None

        # CRT 후처리 설정
        self._crt_processor: Optional["CRTProcessor"] = None
        self._crt_enabled = cfg.get("crt_enabled", False)

        logger.debug(f"{self.__class__.__name__} 초기화: {self.width}x{self.height}@{self.dpi}dpi")

    @abstractmethod
    def render(self, *args, **kwargs) -> Any:
        """
        시각화 렌더링 (추상 메서드)

        서브클래스에서 구현해야 합니다.
        """
        pass

    def create_figure(self, figsize: Optional[tuple] = None) -> tuple:
        """
        matplotlib Figure 생성

        Args:
            figsize: Figure 크기 (인치 단위)

        Returns:
            (fig, ax) 튜플
        """
        if figsize is None:
            figsize = (self.width / self.dpi, self.height / self.dpi)

        self.fig, self.ax = plt.subplots(figsize=figsize, dpi=self.dpi)
        self.fig.patch.set_facecolor(self.bg_color)
        self.ax.set_facecolor(self.bg_color)

        # 축 색상 설정
        self.ax.spines["bottom"].set_color(self.fg_color)
        self.ax.spines["top"].set_color(self.fg_color)
        self.ax.spines["left"].set_color(self.fg_color)
        self.ax.spines["right"].set_color(self.fg_color)
        self.ax.tick_params(colors=self.fg_color)
        self.ax.xaxis.label.set_color(self.fg_color)
        self.ax.yaxis.label.set_color(self.fg_color)

        return self.fig, self.ax

    def save(self, output_path: Path | str, apply_crt: bool = None, **kwargs) -> None:
        """
        시각화 결과를 파일로 저장

        Args:
            output_path: 출력 파일 경로
            apply_crt: CRT 효과 적용 여부 (None이면 self._crt_enabled 사용)
            **kwargs: plt.savefig()에 전달할 추가 인자
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.fig is None:
            raise ValueError("Figure가 생성되지 않았습니다. render()를 먼저 호출하세요.")

        # CRT 후처리 적용 여부 결정
        should_apply_crt = apply_crt if apply_crt is not None else self._crt_enabled

        if should_apply_crt and self._crt_processor is not None:
            # Figure를 이미지로 변환 후 CRT 효과 적용
            self._save_with_crt(output_path, **kwargs)
        else:
            # 기본 저장 옵션
            save_options = {
                "bbox_inches": "tight",
                "facecolor": self.bg_color,
                "edgecolor": "none",
                "dpi": self.dpi,
            }
            save_options.update(kwargs)
            self.fig.savefig(output_path, **save_options)

        logger.info(f"시각화 저장 완료: {output_path}")

    def _save_with_crt(self, output_path: Path, **kwargs) -> None:
        """
        CRT 효과를 적용하여 저장

        Args:
            output_path: 출력 파일 경로
            **kwargs: 추가 옵션
        """
        from io import BytesIO

        from PIL import Image

        # Figure를 메모리에 렌더링
        buf = BytesIO()
        save_options = {
            "bbox_inches": "tight",
            "facecolor": self.bg_color,
            "edgecolor": "none",
            "dpi": self.dpi,
        }
        save_options.update(kwargs)
        self.fig.savefig(buf, format="png", **save_options)
        buf.seek(0)

        # PIL로 로드
        img = Image.open(buf)
        image_array = np.array(img.convert("RGB"))

        # CRT 효과 적용
        processed = self._crt_processor.process(image_array)

        # 저장
        Image.fromarray(processed).save(output_path)
        buf.close()

    def enable_crt(self, processor: "CRTProcessor" = None) -> None:
        """
        CRT 후처리 활성화

        Args:
            processor: CRT 프로세서 (None이면 기본 프로세서 생성)
        """
        if processor is None:
            from src.visualization.retro import create_default_processor
            processor = create_default_processor()

        self._crt_processor = processor
        self._crt_enabled = True
        logger.debug("CRT 후처리 활성화")

    def disable_crt(self) -> None:
        """CRT 후처리 비활성화"""
        self._crt_enabled = False
        logger.debug("CRT 후처리 비활성화")

    @property
    def crt_processor(self) -> Optional["CRTProcessor"]:
        """CRT 프로세서 반환"""
        return self._crt_processor

    def get_image_array(self) -> np.ndarray:
        """
        현재 Figure를 NumPy 배열로 반환

        Returns:
            RGB 이미지 배열 (H, W, 3)
        """
        from io import BytesIO

        from PIL import Image

        if self.fig is None:
            raise ValueError("Figure가 생성되지 않았습니다. render()를 먼저 호출하세요.")

        buf = BytesIO()
        self.fig.savefig(
            buf,
            format="png",
            bbox_inches="tight",
            facecolor=self.bg_color,
            edgecolor="none",
            dpi=self.dpi,
        )
        buf.seek(0)

        img = Image.open(buf)
        image_array = np.array(img.convert("RGB"))
        buf.close()

        return image_array

    def show(self) -> None:
        """시각화 표시"""
        if self.fig is None:
            raise ValueError("Figure가 생성되지 않았습니다. render()를 먼저 호출하세요.")

        plt.show()

    def close(self) -> None:
        """Figure 닫기"""
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None

    def set_title(self, title: str, **kwargs) -> None:
        """
        제목 설정

        Args:
            title: 제목
            **kwargs: 추가 스타일 옵션
        """
        if self.ax is None:
            raise ValueError("Axes가 생성되지 않았습니다.")

        title_options = {"color": self.fg_color, "fontsize": 14, "fontweight": "bold"}
        title_options.update(kwargs)

        self.ax.set_title(title, **title_options)

    def set_labels(self, xlabel: Optional[str] = None, ylabel: Optional[str] = None, **kwargs) -> None:
        """
        축 레이블 설정

        Args:
            xlabel: x축 레이블
            ylabel: y축 레이블
            **kwargs: 추가 스타일 옵션
        """
        if self.ax is None:
            raise ValueError("Axes가 생성되지 않았습니다.")

        label_options = {"color": self.fg_color, "fontsize": 12}
        label_options.update(kwargs)

        if xlabel:
            self.ax.set_xlabel(xlabel, **label_options)
        if ylabel:
            self.ax.set_ylabel(ylabel, **label_options)

    def add_grid(self, **kwargs) -> None:
        """
        그리드 추가

        Args:
            **kwargs: 그리드 스타일 옵션
        """
        if self.ax is None:
            raise ValueError("Axes가 생성되지 않았습니다.")

        grid_options = {"alpha": 0.3, "linestyle": "--", "color": self.fg_color}
        grid_options.update(kwargs)

        self.ax.grid(True, **grid_options)

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close()
