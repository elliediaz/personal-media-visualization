"""
군사용 메인프레임 스타일 데스크톱 GUI 모듈

80~90년대 빈티지 모니터에서 실행되는 군사 목적 메인프레임 느낌의
레트로 GUI를 제공합니다. pygame 기반으로 로컬 실행이 가능합니다.
"""

from src.gui.mainframe_app import MainframeApp, run_app, PhosphorColor

__all__ = [
    "MainframeApp",
    "run_app",
    "PhosphorColor",
]
