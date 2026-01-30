"""
GUI 모듈

군사용 메인프레임 스타일의 레트로 GUI를 제공합니다.
80~90년대 빈티지 모니터에서 실행되는 군사 목적 메인프레임 느낌의
레트로 GUI를 제공합니다. pygame 기반으로 로컬 실행이 가능합니다.
"""

from .mainframe_app import (
    MainframeApp,
    PhosphorColor,
    ColorScheme,
    PHOSPHOR_SCHEMES,
    CRTEffect,
    TerminalFont,
    Panel,
    StatusBar,
    run_app,
)

from .visualizations import (
    VISUALIZATIONS,
    VisualizationCategory,
    VisualizationInfo,
    BaseVisualization,
    create_visualization,
    get_visualization_list,
    get_visualization_by_category,
)

from .audio_input import (
    AudioInputManager,
    AudioInputType,
    AudioDevice,
    AudioState,
    BaseAudioInput,
    DemoAudioInput,
    FileAudioInput,
    DeviceAudioInput,
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
