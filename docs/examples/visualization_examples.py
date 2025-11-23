"""
시각화 예제

다양한 통계적 시각화 예제입니다.
"""

from pathlib import Path

import librosa

from src.analysis.extractor import FeatureExtractor
from src.visualization.statistical.features import FeatureVisualizer
from src.visualization.statistical.rhythm import RhythmVisualizer
from src.visualization.statistical.spectrogram import SpectrogramVisualizer
from src.visualization.statistical.spectrum import SpectrumVisualizer
from src.visualization.statistical.waveform import WaveformVisualizer
from src.utils.logging import setup_logging

# 로깅 설정
logger = setup_logging("example")


def example_waveform():
    """파형 시각화 예제"""
    logger.info("=== 파형 시각화 예제 ===")

    audio_file = Path("data/samples/sample.mp3")
    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 시각화
    with WaveformVisualizer() as viz:
        viz.render(file_path=audio_file)
        viz.save("output/renders/waveform.png")
        logger.info("파형 저장 완료: output/renders/waveform.png")


def example_spectrogram():
    """스펙트로그램 시각화 예제"""
    logger.info("\n=== 스펙트로그램 시각화 예제 ===")

    audio_file = Path("data/samples/sample.mp3")
    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 분석
    extractor = FeatureExtractor()
    result = extractor.extract(audio_file, features=["spectral"])

    # Mel-spectrogram
    with SpectrogramVisualizer() as viz:
        viz.render(result, spec_type="mel")
        viz.save("output/renders/mel_spectrogram.png")
        logger.info("Mel-spectrogram 저장 완료")

    # STFT spectrogram
    with SpectrogramVisualizer() as viz:
        viz.render(result, spec_type="stft")
        viz.save("output/renders/stft_spectrogram.png")
        logger.info("STFT spectrogram 저장 완료")


def example_spectrum():
    """주파수 스펙트럼 시각화 예제"""
    logger.info("\n=== 주파수 스펙트럼 시각화 예제 ===")

    audio_file = Path("data/samples/sample.mp3")
    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 분석
    extractor = FeatureExtractor()
    result = extractor.extract(audio_file, features=["spectral"])

    # 평균 스펙트럼
    with SpectrumVisualizer() as viz:
        viz.render(result)
        viz.save("output/renders/spectrum.png")
        logger.info("주파수 스펙트럼 저장 완료")


def example_features():
    """특성 타임라인 시각화 예제"""
    logger.info("\n=== 특성 타임라인 시각화 예제 ===")

    audio_file = Path("data/samples/sample.mp3")
    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 분석
    extractor = FeatureExtractor()
    result = extractor.extract(audio_file, features=["spectral", "timbre", "rhythm"])

    # 특성 시각화
    features_to_plot = [
        "spectral_centroid",
        "spectral_rolloff",
        "rms_energy",
        "zero_crossing_rate"
    ]

    with FeatureVisualizer() as viz:
        viz.render(result, features=features_to_plot)
        viz.save("output/renders/features.png")
        logger.info("특성 타임라인 저장 완료")


def example_rhythm():
    """리듬 시각화 예제"""
    logger.info("\n=== 리듬 시각화 예제 ===")

    audio_file = Path("data/samples/sample.mp3")
    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 분석
    extractor = FeatureExtractor()
    result = extractor.extract(audio_file, features=["rhythm"])

    # 오디오 데이터 로드 (파형 오버레이용)
    y, sr = librosa.load(str(audio_file), sr=result.sample_rate)

    # 리듬 시각화
    with RhythmVisualizer() as viz:
        viz.render(result, audio_data=y)
        viz.save("output/renders/rhythm.png")
        logger.info("리듬 시각화 저장 완료")


def example_all_visualizations():
    """모든 시각화 한번에 생성"""
    logger.info("\n=== 전체 시각화 예제 ===")

    audio_file = Path("data/samples/sample.mp3")
    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 전체 분석
    logger.info("전체 분석 수행 중...")
    extractor = FeatureExtractor()
    result = extractor.extract(audio_file)

    # 오디오 데이터
    y, sr = librosa.load(str(audio_file), sr=result.sample_rate)

    # 1. 파형
    logger.info("1/5 파형 생성 중...")
    with WaveformVisualizer() as viz:
        viz.render(audio_data=y, sr=sr)
        viz.save("output/renders/all_waveform.png")

    # 2. Mel-spectrogram
    logger.info("2/5 Mel-spectrogram 생성 중...")
    with SpectrogramVisualizer() as viz:
        viz.render(result, spec_type="mel")
        viz.save("output/renders/all_mel_spectrogram.png")

    # 3. 주파수 스펙트럼
    logger.info("3/5 주파수 스펙트럼 생성 중...")
    with SpectrumVisualizer() as viz:
        viz.render(result)
        viz.save("output/renders/all_spectrum.png")

    # 4. 특성 타임라인
    logger.info("4/5 특성 타임라인 생성 중...")
    with FeatureVisualizer() as viz:
        viz.render(result, features=["spectral_centroid", "rms_energy"])
        viz.save("output/renders/all_features.png")

    # 5. 리듬
    logger.info("5/5 리듬 시각화 생성 중...")
    with RhythmVisualizer() as viz:
        viz.render(result, audio_data=y)
        viz.save("output/renders/all_rhythm.png")

    logger.info("\n모든 시각화 완료!")
    logger.info("출력 디렉토리: output/renders/")


if __name__ == "__main__":
    try:
        example_waveform()
        example_spectrogram()
        example_spectrum()
        example_features()
        example_rhythm()

        print("\n" + "=" * 60 + "\n")
        example_all_visualizations()

    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
