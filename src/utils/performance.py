"""
성능 최적화 유틸리티

라즈베리파이 및 저성능 환경을 위한 적응형 품질 관리
"""

import os
import platform
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from src.utils.logging import get_logger

logger = get_logger(__name__)


class PerformanceMode(str, Enum):
    """성능 모드"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    AUTO = "auto"


@dataclass
class QualitySettings:
    """품질 설정"""
    resolution_scale: float
    particle_count: int
    fps_target: int
    effects_enabled: bool
    antialiasing: bool
    shadows: bool


# 성능 모드별 기본 설정
QUALITY_PRESETS = {
    PerformanceMode.LOW: QualitySettings(
        resolution_scale=0.5,
        particle_count=500,
        fps_target=30,
        effects_enabled=False,
        antialiasing=False,
        shadows=False,
    ),
    PerformanceMode.MEDIUM: QualitySettings(
        resolution_scale=0.75,
        particle_count=2000,
        fps_target=45,
        effects_enabled=True,
        antialiasing=False,
        shadows=False,
    ),
    PerformanceMode.HIGH: QualitySettings(
        resolution_scale=1.0,
        particle_count=5000,
        fps_target=60,
        effects_enabled=True,
        antialiasing=True,
        shadows=True,
    ),
}


def detect_raspberry_pi() -> bool:
    """
    라즈베리파이 환경 감지

    Returns:
        라즈베리파이 여부
    """
    try:
        # /proc/device-tree/model 확인
        model_path = "/proc/device-tree/model"
        if os.path.exists(model_path):
            with open(model_path) as f:
                model = f.read().lower()
                if "raspberry pi" in model:
                    logger.info(f"라즈베리파이 감지: {model.strip()}")
                    return True

        # /proc/cpuinfo 확인
        cpuinfo_path = "/proc/cpuinfo"
        if os.path.exists(cpuinfo_path):
            with open(cpuinfo_path) as f:
                cpuinfo = f.read().lower()
                if "raspberry" in cpuinfo or "bcm" in cpuinfo:
                    logger.info("라즈베리파이 감지 (cpuinfo)")
                    return True

        # 플랫폼 확인
        machine = platform.machine().lower()
        if "arm" in machine or "aarch64" in machine:
            # ARM 기반이지만 라즈베리파이인지 추가 확인
            if os.path.exists("/opt/vc/bin/vcgencmd"):
                logger.info("라즈베리파이 감지 (vcgencmd)")
                return True

    except Exception as e:
        logger.debug(f"라즈베리파이 감지 실패: {e}")

    return False


def get_cpu_temperature() -> float | None:
    """
    CPU 온도 조회 (라즈베리파이)

    Returns:
        온도 (섭씨) 또는 None
    """
    try:
        # 라즈베리파이 온도 파일
        temp_path = "/sys/class/thermal/thermal_zone0/temp"
        if os.path.exists(temp_path):
            with open(temp_path) as f:
                temp = int(f.read().strip()) / 1000.0
                return temp
    except Exception:
        pass

    return None


def get_memory_usage() -> float:
    """
    메모리 사용률 조회

    Returns:
        메모리 사용률 (0.0 - 1.0)
    """
    try:
        with open("/proc/meminfo") as f:
            meminfo = {}
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(":")
                    value = int(parts[1])
                    meminfo[key] = value

            total = meminfo.get("MemTotal", 1)
            available = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
            usage = 1.0 - (available / total)
            return usage
    except Exception:
        return 0.5


class PerformanceMonitor:
    """
    성능 모니터

    FPS 측정 및 자동 품질 조절
    """

    def __init__(self, config: dict = None):
        """
        초기화

        Args:
            config: 설정 딕셔너리
        """
        self.config = config or {}
        self.is_raspberry_pi = detect_raspberry_pi()

        # 설정
        self.min_fps = self.config.get("min_fps", 25)
        self.target_fps = self.config.get("target_fps", 30)
        self.check_interval = self.config.get("check_interval", 1.0)
        self.history_size = self.config.get("history_size", 60)

        # 상태
        self.current_mode = PerformanceMode.HIGH
        self.frame_times = deque(maxlen=self.history_size)
        self.last_check_time = time.time()
        self.last_frame_time = time.time()

        # 콜백
        self.on_mode_change: Callable[[PerformanceMode, QualitySettings], None] | None = None

        # 자동 초기화
        if self.is_raspberry_pi:
            self._init_for_raspberry_pi()

        logger.info(f"성능 모니터 초기화 (라즈베리파이: {self.is_raspberry_pi})")

    def _init_for_raspberry_pi(self):
        """라즈베리파이용 초기 설정"""
        # 중간 품질로 시작
        self.current_mode = PerformanceMode.MEDIUM
        logger.info("라즈베리파이: 중간 품질 모드로 시작")

    def tick(self) -> float:
        """
        프레임 틱

        Returns:
            현재 FPS
        """
        current_time = time.time()
        delta = current_time - self.last_frame_time
        self.last_frame_time = current_time

        if delta > 0:
            self.frame_times.append(delta)

        # 주기적으로 성능 체크
        if current_time - self.last_check_time >= self.check_interval:
            self._check_performance()
            self.last_check_time = current_time

        return self.get_fps()

    def get_fps(self) -> float:
        """
        현재 FPS 조회

        Returns:
            평균 FPS
        """
        if not self.frame_times:
            return 0.0

        avg_delta = sum(self.frame_times) / len(self.frame_times)
        if avg_delta > 0:
            return 1.0 / avg_delta
        return 0.0

    def _check_performance(self):
        """성능 체크 및 자동 조절"""
        fps = self.get_fps()
        memory_usage = get_memory_usage()
        temperature = get_cpu_temperature()

        logger.debug(
            f"성능: FPS={fps:.1f}, 메모리={memory_usage*100:.1f}%, "
            f"온도={temperature:.1f}C" if temperature else "온도=N/A"
        )

        # 자동 품질 조절
        new_mode = self._determine_mode(fps, memory_usage, temperature)

        if new_mode != self.current_mode:
            self._change_mode(new_mode)

    def _determine_mode(
        self,
        fps: float,
        memory_usage: float,
        temperature: float | None
    ) -> PerformanceMode:
        """
        적절한 성능 모드 결정

        Args:
            fps: 현재 FPS
            memory_usage: 메모리 사용률
            temperature: CPU 온도

        Returns:
            권장 성능 모드
        """
        # 현재 모드
        current_mode = self.current_mode

        # 온도 기반 조절 (라즈베리파이)
        if temperature is not None:
            if temperature > 80:
                logger.warning(f"CPU 과열: {temperature}C - 저성능 모드로 전환")
                return PerformanceMode.LOW
            elif temperature > 70 and current_mode == PerformanceMode.HIGH:
                return PerformanceMode.MEDIUM

        # 메모리 기반 조절
        if memory_usage > 0.9:
            logger.warning(f"메모리 부족: {memory_usage*100:.0f}% - 저성능 모드로 전환")
            return PerformanceMode.LOW
        elif memory_usage > 0.8 and current_mode == PerformanceMode.HIGH:
            return PerformanceMode.MEDIUM

        # FPS 기반 조절
        if fps < self.min_fps:
            # 성능 저하 - 품질 낮춤
            if current_mode == PerformanceMode.HIGH:
                return PerformanceMode.MEDIUM
            elif current_mode == PerformanceMode.MEDIUM:
                return PerformanceMode.LOW
        elif fps > self.target_fps * 1.2:
            # 여유 있음 - 품질 높임
            if current_mode == PerformanceMode.LOW:
                return PerformanceMode.MEDIUM
            elif current_mode == PerformanceMode.MEDIUM:
                return PerformanceMode.HIGH

        return current_mode

    def _change_mode(self, new_mode: PerformanceMode):
        """
        성능 모드 변경

        Args:
            new_mode: 새 성능 모드
        """
        old_mode = self.current_mode
        self.current_mode = new_mode

        logger.info(f"성능 모드 변경: {old_mode.value} -> {new_mode.value}")

        # 콜백 호출
        if self.on_mode_change:
            settings = QUALITY_PRESETS[new_mode]
            self.on_mode_change(new_mode, settings)

    def get_quality_settings(self) -> QualitySettings:
        """
        현재 품질 설정 조회

        Returns:
            품질 설정
        """
        return QUALITY_PRESETS[self.current_mode]

    def set_mode(self, mode: PerformanceMode):
        """
        성능 모드 수동 설정

        Args:
            mode: 성능 모드
        """
        if mode != PerformanceMode.AUTO:
            self._change_mode(mode)

    def get_system_info(self) -> dict:
        """
        시스템 정보 조회

        Returns:
            시스템 정보 딕셔너리
        """
        return {
            "is_raspberry_pi": self.is_raspberry_pi,
            "platform": platform.system(),
            "machine": platform.machine(),
            "cpu_temperature": get_cpu_temperature(),
            "memory_usage": get_memory_usage(),
            "current_fps": self.get_fps(),
            "current_mode": self.current_mode.value,
            "quality_settings": {
                "resolution_scale": self.get_quality_settings().resolution_scale,
                "particle_count": self.get_quality_settings().particle_count,
                "fps_target": self.get_quality_settings().fps_target,
                "effects_enabled": self.get_quality_settings().effects_enabled,
            }
        }


class FrameRateLimiter:
    """
    프레임 레이트 제한기

    일정한 FPS 유지를 위한 프레임 타이밍 제어
    """

    def __init__(self, target_fps: int = 60):
        """
        초기화

        Args:
            target_fps: 목표 FPS
        """
        self.target_fps = target_fps
        self.frame_duration = 1.0 / target_fps
        self.last_frame_time = time.time()

    def wait(self):
        """다음 프레임까지 대기"""
        current_time = time.time()
        elapsed = current_time - self.last_frame_time
        sleep_time = self.frame_duration - elapsed

        if sleep_time > 0:
            time.sleep(sleep_time)

        self.last_frame_time = time.time()

    def set_target_fps(self, fps: int):
        """
        목표 FPS 설정

        Args:
            fps: 목표 FPS
        """
        self.target_fps = fps
        self.frame_duration = 1.0 / fps


# 전역 성능 모니터 인스턴스
_performance_monitor: PerformanceMonitor | None = None


def get_performance_monitor(config: dict = None) -> PerformanceMonitor:
    """
    전역 성능 모니터 조회

    Args:
        config: 설정 딕셔너리

    Returns:
        성능 모니터 인스턴스
    """
    global _performance_monitor

    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(config)

    return _performance_monitor
