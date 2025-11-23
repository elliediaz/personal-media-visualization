"""
분석 결과 캐싱 시스템

분석 결과를 캐시하여 재사용합니다.
"""

import pickle
import time
from pathlib import Path
from typing import Optional

from src.analysis.result import AnalysisResult
from src.core.config import config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AnalysisCache:
    """
    분석 결과 캐시

    파일 해시를 키로 사용하여 분석 결과를 저장하고 로드합니다.
    """

    def __init__(self, cache_dir: Optional[Path] = None, ttl: Optional[int] = None):
        """
        AnalysisCache 초기화

        Args:
            cache_dir: 캐시 디렉토리 (None이면 설정에서 가져옴)
            ttl: Time-To-Live 초 (None이면 설정에서 가져옴)
        """
        self.cache_dir = cache_dir or Path(config.get("analysis.cache.directory", "data/cache"))
        self.ttl = ttl or config.get("analysis.cache.ttl", 86400)  # 기본 24시간
        self.enabled = config.get("analysis.cache.enabled", True)

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"AnalysisCache 초기화: dir={self.cache_dir}, ttl={self.ttl}s")

    def get(self, file_hash: str) -> Optional[AnalysisResult]:
        """
        캐시에서 분석 결과 가져오기

        Args:
            file_hash: 파일 해시

        Returns:
            AnalysisResult 또는 None (캐시 미스)
        """
        if not self.enabled:
            return None

        cache_file = self.cache_dir / f"{file_hash}.pkl"

        if not cache_file.exists():
            logger.debug(f"캐시 미스: {file_hash[:16]}...")
            return None

        try:
            # 캐시 파일 로드
            with open(cache_file, "rb") as f:
                cached_data = pickle.load(f)

            # TTL 확인
            cached_time = cached_data.get("timestamp", 0)
            if time.time() - cached_time > self.ttl:
                logger.debug(f"캐시 만료: {file_hash[:16]}...")
                cache_file.unlink()  # 만료된 캐시 삭제
                return None

            result = cached_data.get("result")
            logger.info(f"캐시 히트: {file_hash[:16]}...")
            return result

        except Exception as e:
            logger.warning(f"캐시 로드 실패: {e}")
            return None

    def set(self, file_hash: str, result: AnalysisResult) -> None:
        """
        캐시에 분석 결과 저장

        Args:
            file_hash: 파일 해시
            result: 분석 결과
        """
        if not self.enabled:
            return

        cache_file = self.cache_dir / f"{file_hash}.pkl"

        try:
            cached_data = {"timestamp": time.time(), "result": result}

            with open(cache_file, "wb") as f:
                pickle.dump(cached_data, f)

            logger.debug(f"캐시 저장: {file_hash[:16]}...")

        except Exception as e:
            logger.warning(f"캐시 저장 실패: {e}")

    def clear(self) -> None:
        """모든 캐시 삭제"""
        if not self.cache_dir.exists():
            return

        count = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
            count += 1

        logger.info(f"캐시 삭제 완료: {count}개 파일")

    def cleanup_expired(self) -> int:
        """
        만료된 캐시 정리

        Returns:
            삭제된 캐시 파일 수
        """
        if not self.cache_dir.exists():
            return 0

        count = 0
        current_time = time.time()

        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                with open(cache_file, "rb") as f:
                    cached_data = pickle.load(f)

                cached_time = cached_data.get("timestamp", 0)
                if current_time - cached_time > self.ttl:
                    cache_file.unlink()
                    count += 1

            except Exception:
                # 손상된 캐시 파일 삭제
                cache_file.unlink()
                count += 1

        logger.info(f"만료된 캐시 삭제: {count}개")
        return count

    def get_cache_size(self) -> dict:
        """
        캐시 크기 정보

        Returns:
            캐시 크기 정보 딕셔너리
        """
        if not self.cache_dir.exists():
            return {"count": 0, "size_bytes": 0, "size_mb": 0.0}

        count = 0
        total_size = 0

        for cache_file in self.cache_dir.glob("*.pkl"):
            count += 1
            total_size += cache_file.stat().st_size

        return {
            "count": count,
            "size_bytes": total_size,
            "size_mb": total_size / (1024 * 1024),
        }
