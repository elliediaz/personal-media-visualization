"""
설정 시스템 단위 테스트
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.core.config import Config
from src.core.exceptions import ConfigurationException, InvalidConfigurationError


class TestConfig:
    """Config 클래스 테스트"""

    @pytest.fixture
    def temp_config_file(self):
        """임시 설정 파일 생성"""
        config_data = {
            "app": {"name": "TestApp", "version": "1.0.0"},
            "audio": {"sample_rate": 48000, "buffer_size": 1024},
            "nested": {"level1": {"level2": {"value": "deep"}}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        yield Path(temp_path)

        # 정리
        os.unlink(temp_path)

    @pytest.fixture
    def config_instance(self):
        """새로운 Config 인스턴스"""
        # 싱글톤 초기화
        Config._instance = None
        Config._config = {}
        return Config()

    def test_singleton_pattern(self, config_instance):
        """싱글톤 패턴 테스트"""
        config1 = Config()
        config2 = Config()
        assert config1 is config2

    def test_load_from_file(self, config_instance, temp_config_file):
        """파일에서 설정 로드 테스트"""
        config_instance.load_from_file(temp_config_file)

        assert config_instance.get("app.name") == "TestApp"
        assert config_instance.get("audio.sample_rate") == 48000

    def test_load_nonexistent_file(self, config_instance):
        """존재하지 않는 파일 로드 시 예외 발생 테스트"""
        with pytest.raises(InvalidConfigurationError):
            config_instance.load_from_file("nonexistent.yaml")

    def test_get_with_dot_notation(self, config_instance, temp_config_file):
        """점 표기법으로 설정값 가져오기 테스트"""
        config_instance.load_from_file(temp_config_file)

        assert config_instance.get("app.name") == "TestApp"
        assert config_instance.get("nested.level1.level2.value") == "deep"

    def test_get_with_default(self, config_instance):
        """기본값 반환 테스트"""
        assert config_instance.get("nonexistent.key", "default") == "default"

    def test_set_value(self, config_instance):
        """설정값 설정 테스트"""
        config_instance.set("test.key", "value")
        assert config_instance.get("test.key") == "value"

    def test_set_nested_value(self, config_instance):
        """중첩된 설정값 설정 테스트"""
        config_instance.set("a.b.c", 123)
        assert config_instance.get("a.b.c") == 123

    def test_update_config(self, config_instance):
        """설정 업데이트 테스트"""
        config_instance.set("original.value", "old")

        update_data = {"original": {"value": "new"}, "additional": {"key": "value"}}

        config_instance.update(update_data)

        assert config_instance.get("original.value") == "new"
        assert config_instance.get("additional.key") == "value"

    def test_environment_variable_override(self, config_instance, temp_config_file):
        """환경 변수로 설정 오버라이드 테스트"""
        config_instance.load_from_file(temp_config_file)

        # 환경 변수 설정
        os.environ["PMV_AUDIO_SAMPLE_RATE"] = "96000"

        # 환경 변수가 우선
        assert config_instance.get("audio.sample_rate") == 96000

        # 정리
        del os.environ["PMV_AUDIO_SAMPLE_RATE"]

    def test_convert_env_value_boolean(self, config_instance):
        """환경 변수 불린 변환 테스트"""
        assert config_instance._convert_env_value("true") is True
        assert config_instance._convert_env_value("false") is False
        assert config_instance._convert_env_value("yes") is True
        assert config_instance._convert_env_value("no") is False
        assert config_instance._convert_env_value("1") is True
        assert config_instance._convert_env_value("0") is False

    def test_convert_env_value_numbers(self, config_instance):
        """환경 변수 숫자 변환 테스트"""
        assert config_instance._convert_env_value("123") == 123
        assert config_instance._convert_env_value("3.14") == 3.14

    def test_convert_env_value_string(self, config_instance):
        """환경 변수 문자열 변환 테스트"""
        assert config_instance._convert_env_value("hello") == "hello"

    def test_get_all(self, config_instance, temp_config_file):
        """전체 설정 가져오기 테스트"""
        config_instance.load_from_file(temp_config_file)
        all_config = config_instance.get_all()

        assert "app" in all_config
        assert "audio" in all_config

    def test_property_shortcuts(self, config_instance, temp_config_file):
        """프로퍼티 단축키 테스트"""
        config_instance.load_from_file(temp_config_file)

        assert config_instance.audio["sample_rate"] == 48000
        assert config_instance.app["name"] == "TestApp"

    def test_deep_update(self, config_instance):
        """깊은 업데이트 테스트"""
        config_instance.set("a.b.c", 1)
        config_instance.set("a.b.d", 2)

        config_instance.update({"a": {"b": {"c": 10}, "e": 3}})

        assert config_instance.get("a.b.c") == 10  # 업데이트됨
        assert config_instance.get("a.b.d") == 2  # 유지됨
        assert config_instance.get("a.e") == 3  # 추가됨
