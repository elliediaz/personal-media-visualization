"""
메타데이터 추출

오디오 파일의 메타데이터 및 파일 정보를 추출합니다.
"""

import hashlib
from pathlib import Path

import librosa
from mutagen import File as MutagenFile

from src.core.exceptions import AudioException
from src.utils.logging import get_logger

logger = get_logger(__name__)


class MetadataExtractor:
    """메타데이터 추출기"""

    def __init__(self):
        """MetadataExtractor 초기화"""
        logger.debug("MetadataExtractor 초기화 완료")

    def extract(self, file_path: Path | str) -> dict:
        """
        전체 메타데이터 추출

        Args:
            file_path: 오디오 파일 경로

        Returns:
            메타데이터 딕셔너리
        """
        file_path = Path(file_path)
        logger.info(f"메타데이터 추출 시작: {file_path.name}")

        result = {
            "file_info": self.get_file_info(file_path),
            "id3_tags": self.extract_id3_tags(file_path),
            "audio_info": self.get_audio_info(file_path),
            "file_hash": self.compute_file_hash(file_path),
        }

        logger.info("메타데이터 추출 완료")
        return result

    def get_file_info(self, file_path: Path) -> dict:
        """
        파일 정보 가져오기

        Args:
            file_path: 파일 경로

        Returns:
            파일 정보 딕셔너리
        """
        stat = file_path.stat()

        return {
            "name": file_path.name,
            "path": str(file_path.absolute()),
            "size": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "extension": file_path.suffix,
        }

    def extract_id3_tags(self, file_path: Path) -> dict:
        """
        ID3 태그 추출

        Args:
            file_path: 파일 경로

        Returns:
            ID3 태그 딕셔너리
        """
        try:
            audio_file = MutagenFile(str(file_path))

            if audio_file is None or audio_file.tags is None:
                logger.warning("ID3 태그를 찾을 수 없습니다")
                return {}

            tags = {}

            # 공통 태그 매핑
            tag_mapping = {
                "title": ["TIT2", "\xa9nam", "title"],
                "artist": ["TPE1", "\xa9ART", "artist"],
                "album": ["TALB", "\xa9alb", "album"],
                "date": ["TDRC", "\xa9day", "date"],
                "genre": ["TCON", "\xa9gen", "genre"],
                "track": ["TRCK", "trkn", "tracknumber"],
                "album_artist": ["TPE2", "aART", "albumartist"],
                "comment": ["COMM", "\xa9cmt", "comment"],
            }

            for key, possible_keys in tag_mapping.items():
                for pk in possible_keys:
                    if pk in audio_file.tags:
                        value = audio_file.tags[pk]
                        # 리스트인 경우 첫 번째 값 사용
                        if isinstance(value, list) and len(value) > 0:
                            value = value[0]
                        tags[key] = str(value)
                        break

            logger.debug(f"ID3 태그 추출 완료: {len(tags)}개")
            return tags

        except Exception as e:
            logger.warning(f"ID3 태그 추출 실패: {e}")
            return {}

    def get_audio_info(self, file_path: Path) -> dict:
        """
        오디오 파일 정보 가져오기

        Args:
            file_path: 파일 경로

        Returns:
            오디오 정보 딕셔너리
        """
        try:
            # librosa로 정확한 길이 계산
            duration = librosa.get_duration(path=str(file_path))

            # mutagen으로 기술적 정보 추출
            audio_file = MutagenFile(str(file_path))

            info = {"duration": duration}

            if audio_file is not None and hasattr(audio_file.info, "sample_rate"):
                info["sample_rate"] = audio_file.info.sample_rate
            else:
                # librosa로 샘플 레이트 확인
                y, sr = librosa.load(str(file_path), sr=None, duration=0.1)
                info["sample_rate"] = sr

            if audio_file is not None and hasattr(audio_file.info, "bitrate"):
                info["bitrate"] = audio_file.info.bitrate
                info["bitrate_kbps"] = audio_file.info.bitrate // 1000

            if audio_file is not None and hasattr(audio_file.info, "channels"):
                info["channels"] = audio_file.info.channels

            logger.debug(
                f"오디오 정보: {duration:.2f}초, "
                f"{info.get('sample_rate', 'N/A')}Hz"
            )

            return info

        except Exception as e:
            logger.error(f"오디오 정보 추출 실패: {e}")
            raise AudioException(f"오디오 정보 추출 실패: {e}")

    def compute_file_hash(self, file_path: Path, algorithm: str = "md5") -> str:
        """
        파일 해시 계산

        Args:
            file_path: 파일 경로
            algorithm: 해시 알고리즘 (md5, sha256)

        Returns:
            파일 해시 값
        """
        if algorithm == "md5":
            hasher = hashlib.md5()
        elif algorithm == "sha256":
            hasher = hashlib.sha256()
        else:
            raise ValueError(f"지원하지 않는 해시 알고리즘: {algorithm}")

        with open(file_path, "rb") as f:
            # 큰 파일을 위한 청크 단위 읽기
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)

        file_hash = hasher.hexdigest()
        logger.debug(f"파일 해시 ({algorithm}): {file_hash[:16]}...")

        return file_hash

    def extract_cover_art(self, file_path: Path, output_path: Path | None = None) -> bytes | None:
        """
        커버 아트 추출

        Args:
            file_path: 파일 경로
            output_path: 저장할 경로 (None이면 저장하지 않음)

        Returns:
            커버 아트 바이너리 데이터 (없으면 None)
        """
        try:
            audio_file = MutagenFile(str(file_path))

            if audio_file is None or audio_file.tags is None:
                return None

            # MP3 (ID3)
            if "APIC:" in audio_file.tags:
                cover_data = audio_file.tags["APIC:"].data
            # M4A (MP4)
            elif "covr" in audio_file.tags:
                cover_data = bytes(audio_file.tags["covr"][0])
            # FLAC
            elif hasattr(audio_file, "pictures") and len(audio_file.pictures) > 0:
                cover_data = audio_file.pictures[0].data
            else:
                logger.debug("커버 아트를 찾을 수 없습니다")
                return None

            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(cover_data)
                logger.info(f"커버 아트 저장: {output_path}")

            logger.debug(f"커버 아트 추출 완료: {len(cover_data)} bytes")
            return cover_data

        except Exception as e:
            logger.warning(f"커버 아트 추출 실패: {e}")
            return None
