"""
설정 관리 시스템

YAML 파일 기반 설정 로드 및 관리
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

from src.core.exceptions import ConfigurationException, InvalidConfigurationError

# 환경 변수 로드
load_dotenv()


class Config:
    """설정 관리 클래스"""

    _instance: Optional["Config"] = None
    _config: dict[str, Any] = {}

    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """초기화"""
        if not self._config:
            self._load_default_config()

    def _load_default_config(self) -> None:
        """기본 설정 파일 로드"""
        config_path = Path(__file__).parent.parent.parent / "config" / "default.yaml"
        self.load_from_file(config_path)

    def load_from_file(self, config_path: Path | str) -> None:
        """
        YAML 파일에서 설정 로드

        Args:
            config_path: 설정 파일 경로

        Raises:
            ConfigurationException: 파일 로드 실패 시
        """
        try:
            config_path = Path(config_path)
            if not config_path.exists():
                raise InvalidConfigurationError(
                    f"설정 파일을 찾을 수 없습니다: {config_path}"
                )

            with open(config_path, encoding="utf-8") as f:
                loaded_config = yaml.safe_load(f)

            if loaded_config:
                self._config.update(loaded_config)

        except yaml.YAMLError as e:
            raise ConfigurationException(f"YAML 파싱 오류: {e}")
        except Exception as e:
            raise ConfigurationException(f"설정 파일 로드 실패: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        설정값 가져오기 (점 표기법 지원)

        Args:
            key: 설정 키 (예: "audio.sample_rate")
            default: 기본값

        Returns:
            설정값 또는 기본값
        """
        # 환경 변수 확인 (PMV_ 접두사)
        env_key = f"PMV_{key.replace('.', '_').upper()}"
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_env_value(env_value)

        # 설정 파일에서 가져오기
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        설정값 설정 (점 표기법 지원)

        Args:
            key: 설정 키 (예: "audio.sample_rate")
            value: 설정할 값
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def _convert_env_value(self, value: str) -> Any:
        """
        환경 변수 값을 적절한 타입으로 변환

        Args:
            value: 환경 변수 값

        Returns:
            변환된 값
        """
        # 불린 변환
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # 숫자 변환
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        return value

    def get_all(self) -> dict[str, Any]:
        """
        전체 설정 가져오기

        Returns:
            전체 설정 딕셔너리
        """
        return self._config.copy()

    def update(self, config_dict: dict[str, Any]) -> None:
        """
        설정 업데이트

        Args:
            config_dict: 업데이트할 설정 딕셔너리
        """
        self._deep_update(self._config, config_dict)

    def _deep_update(self, base: dict, update: dict) -> None:
        """
        딕셔너리 깊은 업데이트

        Args:
            base: 기본 딕셔너리
            update: 업데이트 딕셔너리
        """
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    @property
    def audio(self) -> dict[str, Any]:
        """오디오 설정"""
        return self.get("audio", {})

    @property
    def analysis(self) -> dict[str, Any]:
        """분석 설정"""
        return self.get("analysis", {})

    @property
    def visualization(self) -> dict[str, Any]:
        """시각화 설정"""
        return self.get("visualization", {})

    @property
    def api(self) -> dict[str, Any]:
        """API 설정"""
        return self.get("api", {})

    @property
    def paths(self) -> dict[str, Any]:
        """경로 설정"""
        return self.get("paths", {})

    @property
    def performance(self) -> dict[str, Any]:
        """성능 설정"""
        return self.get("performance", {})


# 전역 설정 인스턴스
config = Config()
