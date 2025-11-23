"""
기본 오디오 재생 예제

AudioPlayer를 사용하여 기본적인 오디오 재생을 수행하는 예제입니다.
"""

import time
from pathlib import Path

from src.audio.player import AudioPlayer
from src.utils.logging import setup_logging

# 로깅 설정
logger = setup_logging("example")


def example_basic_playback():
    """기본 재생 예제"""
    logger.info("=== 기본 재생 예제 ===")

    # 플레이어 생성
    player = AudioPlayer()

    # 샘플 오디오 파일 경로 (실제 파일로 교체 필요)
    audio_file = Path("data/samples/sample.mp3")

    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        logger.info("data/samples/ 디렉토리에 sample.mp3 파일을 추가하세요")
        return

    # 파일 로드
    logger.info(f"파일 로드: {audio_file.name}")
    player.load(audio_file)

    # 재생
    logger.info("재생 시작")
    player.play()

    # 5초간 재생
    time.sleep(5)

    # 일시정지
    logger.info(f"일시정지 (현재 위치: {player.position:.2f}초)")
    player.pause()

    # 2초 대기
    time.sleep(2)

    # 재생 재개
    logger.info("재생 재개")
    player.play()

    # 3초간 더 재생
    time.sleep(3)

    # 정지
    logger.info("재생 정지")
    player.stop()


def example_with_callbacks():
    """콜백을 사용한 예제"""
    logger.info("=== 콜백 예제 ===")

    player = AudioPlayer()
    audio_file = Path("data/samples/sample.mp3")

    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 콜백 함수 정의
    def on_play():
        logger.info("▶ 재생 시작됨")

    def on_pause():
        logger.info("⏸ 일시정지됨")

    def on_stop():
        logger.info("⏹ 정지됨")

    def on_end():
        logger.info("✓ 재생 완료")

    # 콜백 설정
    player.set_callback(
        on_play=on_play, on_pause=on_pause, on_stop=on_stop, on_end=on_end
    )

    # 파일 로드 및 재생
    player.load(audio_file)
    player.play()

    time.sleep(3)
    player.pause()

    time.sleep(1)
    player.play()

    time.sleep(2)
    player.stop()


def example_volume_control():
    """볼륨 제어 예제"""
    logger.info("=== 볼륨 제어 예제 ===")

    player = AudioPlayer()
    audio_file = Path("data/samples/sample.mp3")

    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    player.load(audio_file)

    # 볼륨 100%로 재생
    player.volume = 1.0
    logger.info(f"볼륨 {player.volume * 100:.0f}%로 재생")
    player.play()
    time.sleep(2)

    # 볼륨 50%로 감소
    player.volume = 0.5
    logger.info(f"볼륨 {player.volume * 100:.0f}%로 감소")
    time.sleep(2)

    # 볼륨 25%로 감소
    player.volume = 0.25
    logger.info(f"볼륨 {player.volume * 100:.0f}%로 감소")
    time.sleep(2)

    player.stop()


def example_seek():
    """탐색 기능 예제"""
    logger.info("=== 탐색 예제 ===")

    player = AudioPlayer()
    audio_file = Path("data/samples/sample.mp3")

    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    player.load(audio_file)
    player.play()

    # 처음부터 재생
    logger.info("0초부터 재생")
    time.sleep(2)

    # 10초 위치로 이동
    logger.info("10초 위치로 이동")
    player.seek(10.0)
    time.sleep(2)

    # 30초 위치로 이동
    logger.info("30초 위치로 이동")
    player.seek(30.0)
    time.sleep(2)

    player.stop()


if __name__ == "__main__":
    # 예제 실행
    try:
        example_basic_playback()
        print("\n")

        example_with_callbacks()
        print("\n")

        example_volume_control()
        print("\n")

        example_seek()

    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
