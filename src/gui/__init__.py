"""
GUI 모듈

군사용 메인프레임 스타일의 레트로 GUI를 제공합니다.
80~90년대 빈티지 모니터에서 실행되는 군사 목적 메인프레임 느낌의
레트로 GUI를 제공합니다. pygame 기반으로 로컬 실행이 가능합니다.
"""

from .audio_input import (
    AudioDevice,
    AudioInputManager,
    AudioInputType,
    AudioState,
    BaseAudioInput,
    DemoAudioInput,
    DeviceAudioInput,
    FileAudioInput,
)
from .mainframe_app import (
    PHOSPHOR_SCHEMES,
    ColorScheme,
    CRTEffect,
    MainframeApp,
    Panel,
    PhosphorColor,
    StatusBar,
    TerminalFont,
    run_app,
)
from .visualizations import (
    VISUALIZATIONS,
    BaseVisualization,
    VisualizationCategory,
    VisualizationInfo,
    create_visualization,
    get_visualization_by_category,
    get_visualization_list,
)

__all__ = [
    # Main app
    "MainframeApp",
    "PhosphorColor",
    "ColorScheme",
    "PHOSPHOR_SCHEMES",
    "CRTEffect",
    "TerminalFont",
    "Panel",
    "StatusBar",
    "run_app",
    # Visualizations
    "VISUALIZATIONS",
    "VisualizationCategory",
    "VisualizationInfo",
    "BaseVisualization",
    "create_visualization",
    "get_visualization_list",
    "get_visualization_by_category",
    # Audio input
    "AudioInputManager",
    "AudioInputType",
    "AudioDevice",
    "AudioState",
    "BaseAudioInput",
    "DemoAudioInput",
    "FileAudioInput",
    "DeviceAudioInput",
]
