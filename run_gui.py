#!/usr/bin/env python
"""
Personal Media Visualization - 메인프레임 스타일 GUI 실행

80~90년대 군사용 메인프레임/터미널 스타일의 레트로 GUI를 실행합니다.
CRT 인광 효과, 스캔라인, 노이즈 등을 포함한 빈티지 모니터 시뮬레이션.
52개의 다양한 시각화 스타일을 지원합니다.

사용법:
    python run_gui.py [옵션]

옵션:
    --phosphor, -p  : 인광체 색상 (green, amber, white, blue) [기본값: green]
    --width, -W     : 창 너비 [기본값: 1024]
    --height, -H    : 창 높이 [기본값: 768]
    --no-crt        : CRT 효과 비활성화

단축키:
    F1/F2/LEFT/RIGHT : 시각화 전환 (52개 스타일)
    F3              : CRT 효과 토글
    F4              : 인광체 색상 변경
    F5              : 설정 화면 (오디오 입력 선택)
    F11             : 전체 창 전체 화면 토글
    F12             : 시각화 전용 전체 화면 토글
    SPACE           : 재생/일시정지 (파일 모드)
    ESC             : 종료 (시각화 전용 모드에서는 복귀)
"""

import argparse
import importlib.util
import sys


def main():
    parser = argparse.ArgumentParser(
        description="군사용 메인프레임 스타일 오디오 시각화 GUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
인광체 색상:
  green  - 클래식 그린 (P1 인광체)
  amber  - 앰버 (P3 인광체)
  white  - 화이트 (P4 인광체)
  blue   - 군사용 블루

오디오 입력:
  F5 키를 눌러 설정 화면에서 선택:
  - DEMO MODE: 합성 파형 생성
  - OPEN FILE: 오디오 파일 열기 (mp3, wav, flac, ogg)
  - LOOPBACK: Windows 시스템 오디오 캡처
  - MIC: 마이크 입력

예시:
  python run_gui.py                     # 기본 실행 (그린)
  python run_gui.py -p amber            # 앰버 인광체
  python run_gui.py -p blue --no-crt    # 블루, CRT 효과 없이
  python run_gui.py -W 1280 -H 960      # 큰 해상도
        """
    )

    parser.add_argument(
        "-p", "--phosphor",
        choices=["green", "amber", "white", "blue"],
        default="green",
        help="인광체 색상 (기본값: green)"
    )
    parser.add_argument(
        "-W", "--width",
        type=int,
        default=1024,
        help="창 너비 (기본값: 1024)"
    )
    parser.add_argument(
        "-H", "--height",
        type=int,
        default=768,
        help="창 높이 (기본값: 768)"
    )
    parser.add_argument(
        "--no-crt",
        action="store_true",
        help="CRT 효과 비활성화"
    )
    parser.add_argument(
        "--fullscreen",
        action="store_true",
        help="전체 화면 모드"
    )

    args = parser.parse_args()

    # pygame 임포트 체크
    if importlib.util.find_spec("pygame") is None:
        print("=" * 60)
        print("오류: pygame이 설치되어 있지 않습니다.")
        print()
        print("설치 방법:")
        print("  pip install pygame")
        print("=" * 60)
        sys.exit(1)

    # numpy 임포트 체크
    if importlib.util.find_spec("numpy") is None:
        print("=" * 60)
        print("오류: numpy가 설치되어 있지 않습니다.")
        print()
        print("설치 방법:")
        print("  pip install numpy")
        print("=" * 60)
        sys.exit(1)

    # GUI 모듈 임포트
    try:
        from src.gui.mainframe_app import run_app
    except ImportError as e:
        print(f"모듈 임포트 오류: {e}")
        print()
        print("프로젝트 루트 디렉토리에서 실행하세요:")
        print("  cd personal-media-visualization")
        print("  python run_gui.py")
        sys.exit(1)

    # 시작 메시지
    print()
    print("█" * 60)
    print("█                                                          █")
    print("█    MAINFRAME AUDIO VISUALIZATION SYSTEM                  █")
    print("█    Military-Grade Terminal Emulation v2.0                █")
    print("█    52 Visualization Styles Available                     █")
    print("█                                                          █")
    print("█" * 60)
    print()
    print(f"  인광체 색상 : {args.phosphor.upper()}")
    print(f"  해상도      : {args.width}x{args.height}")
    print(f"  CRT 효과    : {'ON' if not args.no_crt else 'OFF'}")
    print()
    print("  단축키:")
    print("    F1/F2   - 시각화 이전/다음")
    print("    F3      - CRT 효과 토글")
    print("    F4      - 인광체 색상 변경")
    print("    F5      - 설정 (오디오 입력 선택)")
    print("    F11     - 전체 창 전체 화면")
    print("    F12     - 시각화 전용 전체 화면")
    print("    SPACE   - 재생/일시정지")
    print("    ESC     - 종료")
    print()
    print("=" * 60)
    print("  시스템 초기화 중...")
    print()

    # GUI 실행
    run_app(
        phosphor=args.phosphor,
        width=args.width,
        height=args.height,
        crt_effects=not args.no_crt,
    )

    print()
    print("  시스템 종료 완료.")
    print("=" * 60)


if __name__ == "__main__":
    main()
