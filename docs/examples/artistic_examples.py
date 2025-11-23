"""
예술적 시각화 예제

오디오 반응형 미디어 아트 시각화 예제
"""

from pathlib import Path

from src.analysis.extractor import FeatureExtractor
from src.visualization.artistic.circles import CircleVisualizer
from src.visualization.artistic.particles import ParticleVisualizer
from src.visualization.artistic.waves import WaveInterferenceVisualizer
from src.utils.logging import setup_logging

# 로깅 설정
logger = setup_logging("example")


def example_particles():
    """파티클 시각화 예제"""
    logger.info("=== 파티클 시각화 예제 ===")

    audio_file = Path("data/samples/sample.mp3")
    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 분석
    extractor = FeatureExtractor()
    result = extractor.extract(audio_file)

    # 파티클 시각화
    with ParticleVisualizer() as viz:
        viz.render(result, num_particles=2000)
        viz.save("output/renders/artistic_particles.png")
        logger.info("파티클 시각화 저장 완료")


def example_circles():
    """동심원 시각화 예제"""
    logger.info("\n=== 동심원 시각화 예제 ===")

    audio_file = Path("data/samples/sample.mp3")
    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 분석
    extractor = FeatureExtractor()
    result = extractor.extract(audio_file, features=["rhythm", "harmonic"])

    # 동심원 시각화
    with CircleVisualizer() as viz:
        viz.render(result, num_circles=60)
        viz.save("output/renders/artistic_circles.png")
        logger.info("동심원 시각화 저장 완료")


def example_wave_interference():
    """파동 간섭 시각화 예제"""
    logger.info("\n=== 파동 간섭 시각화 예제 ===")

    audio_file = Path("data/samples/sample.mp3")
    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 분석
    extractor = FeatureExtractor()
    result = extractor.extract(audio_file)

    # 파동 간섭 시각화
    with WaveInterferenceVisualizer() as viz:
        viz.render(result, resolution=600)
        viz.save("output/renders/artistic_waves.png")
        logger.info("파동 간섭 시각화 저장 완료")


def example_all_artistic():
    """모든 예술적 시각화 생성"""
    logger.info("\n=== 전체 예술적 시각화 ===")

    audio_file = Path("data/samples/sample.mp3")
    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 전체 분석
    logger.info("전체 분석 수행 중...")
    extractor = FeatureExtractor()
    result = extractor.extract(audio_file)

    # 1. 파티클
    logger.info("1/3 파티클 생성 중...")
    with ParticleVisualizer() as viz:
        viz.render(result, num_particles=3000)
        viz.save("output/renders/art_all_particles.png")

    # 2. 동심원
    logger.info("2/3 동심원 생성 중...")
    with CircleVisualizer() as viz:
        viz.render(result, num_circles=80)
        viz.save("output/renders/art_all_circles.png")

    # 3. 파동 간섭
    logger.info("3/3 파동 간섭 생성 중...")
    with WaveInterferenceVisualizer() as viz:
        viz.render(result, resolution=800, cmap="plasma")
        viz.save("output/renders/art_all_waves.png")

    logger.info("\n모든 예술적 시각화 완료!")
    logger.info("출력 디렉토리: output/renders/")


def example_comparison():
    """다양한 스타일 비교"""
    logger.info("\n=== 스타일 비교 예제 ===")

    audio_file = Path("data/samples/sample.mp3")
    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    extractor = FeatureExtractor()
    result = extractor.extract(audio_file)

    # 파동 간섭 - 다양한 컬러맵
    colormaps = ["twilight", "plasma", "viridis", "coolwarm"]

    for i, cmap in enumerate(colormaps):
        logger.info(f"컬러맵 {i+1}/4: {cmap}")
        with WaveInterferenceVisualizer() as viz:
            viz.render(result, resolution=400, cmap=cmap)
            viz.save(f"output/renders/waves_{cmap}.png")

    logger.info("스타일 비교 완료")


if __name__ == "__main__":
    try:
        example_particles()
        example_circles()
        example_wave_interference()

        print("\n" + "=" * 60 + "\n")
        example_all_artistic()

        print("\n" + "=" * 60 + "\n")
        example_comparison()

    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
