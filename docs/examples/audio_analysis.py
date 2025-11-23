"""
오디오 분석 예제

FeatureExtractor를 사용하여 오디오 파일을 분석하는 예제입니다.
"""

from pathlib import Path

from src.analysis.cache import AnalysisCache
from src.analysis.extractor import FeatureExtractor
from src.analysis.metadata import MetadataExtractor
from src.utils.logging import setup_logging

# 로깅 설정
logger = setup_logging("example")


def example_full_analysis():
    """전체 분석 예제"""
    logger.info("=== 전체 오디오 분석 예제 ===")

    # 샘플 파일
    audio_file = Path("data/samples/sample.mp3")

    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        logger.info("data/samples/ 디렉토리에 sample.mp3 파일을 추가하세요")
        return

    # 특성 추출기 생성
    extractor = FeatureExtractor()

    # 진행률 콜백
    def progress_callback(feature_name: str, progress: float):
        logger.info(f"  {feature_name}: {progress * 100:.0f}%")

    # 분석 수행
    logger.info("분석 시작...")
    result = extractor.extract(audio_file, progress_callback=progress_callback)

    # 결과 요약 출력
    logger.info("\n" + result.summary())

    # 특정 특성 접근
    logger.info("\n특성 접근 예제:")
    logger.info(f"템포: {result.get_feature('rhythm.tempo'):.1f} BPM")
    logger.info(f"키: {result.get_feature('harmonic.key')}")
    logger.info(f"아티스트: {result.get_feature('metadata.id3_tags.artist', 'Unknown')}")

    # JSON으로 저장
    output_path = Path("output/exports/analysis_result.json")
    result.to_json(output_path)
    logger.info(f"\n분석 결과 저장: {output_path}")


def example_selective_analysis():
    """선택적 분석 예제"""
    logger.info("\n=== 선택적 분석 예제 ===")

    audio_file = Path("data/samples/sample.mp3")

    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    extractor = FeatureExtractor()

    # 리듬과 메타데이터만 분석
    logger.info("리듬 및 메타데이터 분석...")
    result = extractor.extract(audio_file, features=["rhythm", "metadata"])

    logger.info(f"템포: {result.rhythm.get('tempo'):.1f} BPM")
    logger.info(f"비트 수: {len(result.rhythm.get('beats', []))}개")


def example_with_cache():
    """캐시 사용 예제"""
    logger.info("\n=== 캐시 사용 예제 ===")

    audio_file = Path("data/samples/sample.mp3")

    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 캐시 초기화
    cache = AnalysisCache()
    extractor = FeatureExtractor()

    # 메타데이터 추출기로 파일 해시 계산
    metadata_extractor = MetadataExtractor()
    file_hash = metadata_extractor.compute_file_hash(audio_file)

    # 캐시에서 확인
    cached_result = cache.get(file_hash)

    if cached_result:
        logger.info("캐시에서 결과 로드!")
        result = cached_result
    else:
        logger.info("새로 분석 수행...")
        result = extractor.extract(audio_file)
        cache.set(file_hash, result)
        logger.info("캐시에 저장 완료")

    logger.info(result.summary())

    # 캐시 정보
    cache_info = cache.get_cache_size()
    logger.info(f"\n캐시 정보: {cache_info['count']}개 파일, {cache_info['size_mb']:.2f}MB")


def example_metadata_only():
    """메타데이터만 추출 예제"""
    logger.info("\n=== 메타데이터 추출 예제 ===")

    audio_file = Path("data/samples/sample.mp3")

    if not audio_file.exists():
        logger.error(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 메타데이터 추출기
    metadata_extractor = MetadataExtractor()
    metadata = metadata_extractor.extract(audio_file)

    # 파일 정보
    file_info = metadata["file_info"]
    logger.info(f"파일명: {file_info['name']}")
    logger.info(f"크기: {file_info['size_mb']:.2f}MB")

    # 오디오 정보
    audio_info = metadata["audio_info"]
    logger.info(f"길이: {audio_info['duration']:.2f}초")
    logger.info(f"샘플레이트: {audio_info.get('sample_rate', 'N/A')}Hz")
    logger.info(f"비트레이트: {audio_info.get('bitrate_kbps', 'N/A')}kbps")

    # ID3 태그
    id3_tags = metadata["id3_tags"]
    if id3_tags:
        logger.info("\nID3 태그:")
        for key, value in id3_tags.items():
            logger.info(f"  {key}: {value}")
    else:
        logger.info("\nID3 태그 없음")


if __name__ == "__main__":
    try:
        example_full_analysis()
        print("\n" + "=" * 60 + "\n")

        example_selective_analysis()
        print("\n" + "=" * 60 + "\n")

        example_with_cache()
        print("\n" + "=" * 60 + "\n")

        example_metadata_only()

    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
