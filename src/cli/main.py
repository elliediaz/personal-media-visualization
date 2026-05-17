"""
CLI 메인 모듈

click 기반 명령행 인터페이스
"""

import json
import sys
from pathlib import Path

import click

from src.core.config import config
from src.utils.logging import get_logger, setup_logging

# 로깅 설정
setup_logging("cli")
logger = get_logger(__name__)


@click.group()
@click.version_option(version=config.get("app.version", "0.1.0"))
def cli():
    """Personal Media Visualization - 오디오 분석 및 시각화 도구"""
    pass


@cli.command()
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("--volume", "-v", default=0.8, help="볼륨 (0.0 ~ 1.0)")
def play(audio_file: str, volume: float):
    """
    오디오 파일 재생

    AUDIO_FILE: 재생할 오디오 파일 경로
    """
    try:
        from src.audio.player import AudioPlayer

        player = AudioPlayer()
        player.load(audio_file)
        player.volume = volume

        click.echo(f"재생 중: {Path(audio_file).name}")
        click.echo("중지하려면 Ctrl+C를 누르세요.")

        player.play()

        # 재생이 끝날 때까지 대기
        import time

        while player.is_playing:
            time.sleep(0.1)

        click.echo("재생 완료")

    except KeyboardInterrupt:
        click.echo("\n재생 중지")
    except Exception as e:
        click.echo(f"오류: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="출력 파일 경로")
@click.option(
    "--features",
    "-f",
    multiple=True,
    help="추출할 특성 (spectral, rhythm, harmonic, timbre, metadata)",
)
@click.option("--format", "output_format", default="json", help="출력 형식 (json, yaml)")
def analyze(
    audio_file: str,
    output: str | None,
    features: tuple,
    output_format: str,
):
    """
    오디오 파일 분석

    AUDIO_FILE: 분석할 오디오 파일 경로
    """
    try:
        from src.analysis.extractor import FeatureExtractor

        click.echo(f"분석 중: {Path(audio_file).name}")

        extractor = FeatureExtractor()
        feature_list = list(features) if features else None
        result = extractor.extract(audio_file, features=feature_list)

        # 결과를 딕셔너리로 변환
        result_dict = result.to_dict()

        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                if output_format == "yaml":
                    import yaml

                    yaml.dump(result_dict, f, allow_unicode=True, default_flow_style=False)
                else:
                    json.dump(result_dict, f, indent=2, ensure_ascii=False, default=str)

            click.echo(f"분석 결과 저장: {output_path}")
        else:
            click.echo(json.dumps(result_dict, indent=2, ensure_ascii=False, default=str))

    except Exception as e:
        click.echo(f"오류: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("audio_file", type=click.Path(exists=True))
@click.option(
    "--type",
    "viz_type",
    default="spectrogram",
    help="시각화 타입 (waveform, spectrogram, spectrum, features, particles, circles, waves)",
)
@click.option("--output", "-o", type=click.Path(), required=True, help="출력 파일 경로")
@click.option("--width", default=1920, help="너비 (px)")
@click.option("--height", default=1080, help="높이 (px)")
@click.option("--dpi", default=100, help="DPI")
def visualize(
    audio_file: str,
    viz_type: str,
    output: str,
    width: int,
    height: int,
    dpi: int,
):
    """
    오디오 시각화 생성

    AUDIO_FILE: 시각화할 오디오 파일 경로
    """
    try:
        from src.analysis.extractor import FeatureExtractor

        click.echo(f"시각화 생성 중: {Path(audio_file).name} -> {viz_type}")

        # 분석 수행
        extractor = FeatureExtractor()
        result = extractor.extract(audio_file)

        # 시각화 설정
        viz_config = {"width": width, "height": height, "dpi": dpi}

        # 시각화 타입에 따른 처리
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if viz_type == "waveform":
            from src.visualization.statistical.waveform import WaveformVisualizer

            viz = WaveformVisualizer(viz_config)
            viz.render(result)
            viz.save(output_path)

        elif viz_type == "spectrogram":
            from src.visualization.statistical.spectrogram import SpectrogramVisualizer

            viz = SpectrogramVisualizer(viz_config)
            viz.render(result)
            viz.save(output_path)

        elif viz_type == "spectrum":
            from src.visualization.statistical.spectrum import SpectrumVisualizer

            viz = SpectrumVisualizer(viz_config)
            viz.render(result)
            viz.save(output_path)

        elif viz_type == "features":
            from src.visualization.statistical.features import FeaturesVisualizer

            viz = FeaturesVisualizer(viz_config)
            viz.render(result)
            viz.save(output_path)

        elif viz_type == "particles":
            from src.visualization.artistic.particles import ParticleVisualizer

            viz = ParticleVisualizer(viz_config)
            viz.render(result)
            viz.save(output_path)

        elif viz_type == "circles":
            from src.visualization.artistic.circles import CircleVisualizer

            viz = CircleVisualizer(viz_config)
            viz.render(result)
            viz.save(output_path)

        elif viz_type == "waves":
            from src.visualization.artistic.waves import WaveVisualizer

            viz = WaveVisualizer(viz_config)
            viz.render(result)
            viz.save(output_path)

        else:
            click.echo(f"알 수 없는 시각화 타입: {viz_type}", err=True)
            sys.exit(1)

        click.echo(f"시각화 저장 완료: {output_path}")

    except Exception as e:
        click.echo(f"오류: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--output-dir", "-o", type=click.Path(), default="output/batch", help="출력 디렉토리")
@click.option(
    "--visualizers",
    "-v",
    default="all",
    help="사용할 시각화 (all, statistical, artistic, 또는 쉼표로 구분된 목록)",
)
def batch(directory: str, output_dir: str, visualizers: str):
    """
    디렉토리 내 오디오 파일 일괄 처리

    DIRECTORY: 처리할 오디오 파일이 있는 디렉토리
    """
    try:
        from src.audio.formats import SUPPORTED_FORMATS

        input_dir = Path(directory)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 오디오 파일 검색
        audio_files = []
        for fmt in SUPPORTED_FORMATS:
            audio_files.extend(input_dir.glob(f"*.{fmt}"))

        if not audio_files:
            click.echo("처리할 오디오 파일이 없습니다.")
            return

        click.echo(f"총 {len(audio_files)}개 파일 발견")

        # 시각화 타입 결정
        if visualizers == "all":
            viz_types = ["waveform", "spectrogram", "spectrum", "particles"]
        elif visualizers == "statistical":
            viz_types = ["waveform", "spectrogram", "spectrum"]
        elif visualizers == "artistic":
            viz_types = ["particles", "circles", "waves"]
        else:
            viz_types = [v.strip() for v in visualizers.split(",")]

        # 각 파일 처리
        from src.analysis.extractor import FeatureExtractor

        extractor = FeatureExtractor()

        for i, audio_file in enumerate(audio_files, 1):
            click.echo(f"[{i}/{len(audio_files)}] 처리 중: {audio_file.name}")

            try:
                # 분석
                result = extractor.extract(audio_file)

                # 시각화
                for viz_type in viz_types:
                    output_file = output_path / f"{audio_file.stem}_{viz_type}.png"

                    # 시각화 생성 (간략화)
                    if viz_type == "waveform":
                        from src.visualization.statistical.waveform import WaveformVisualizer

                        viz = WaveformVisualizer()
                    elif viz_type == "spectrogram":
                        from src.visualization.statistical.spectrogram import (
                            SpectrogramVisualizer,
                        )

                        viz = SpectrogramVisualizer()
                    elif viz_type == "spectrum":
                        from src.visualization.statistical.spectrum import SpectrumVisualizer

                        viz = SpectrumVisualizer()
                    elif viz_type == "particles":
                        from src.visualization.artistic.particles import ParticleVisualizer

                        viz = ParticleVisualizer()
                    else:
                        continue

                    viz.render(result)
                    viz.save(output_file)
                    viz.close()

            except Exception as e:
                click.echo(f"  오류: {e}", err=True)

        click.echo(f"일괄 처리 완료. 결과: {output_path}")

    except Exception as e:
        click.echo(f"오류: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--host", default="0.0.0.0", help="서버 호스트")
@click.option("--port", default=8000, help="서버 포트")
@click.option("--reload", is_flag=True, help="자동 리로드 활성화")
def serve(host: str, port: int, reload: bool):
    """API 서버 시작"""
    try:
        import uvicorn

        click.echo(f"서버 시작: http://{host}:{port}")
        click.echo("API 문서: http://localhost:{port}/docs")

        uvicorn.run(
            "src.api.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
        )

    except Exception as e:
        click.echo(f"오류: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("audio_file", type=click.Path(exists=True))
def info(audio_file: str):
    """오디오 파일 정보 표시"""
    try:
        from src.analysis.metadata import MetadataExtractor

        extractor = MetadataExtractor()
        metadata = extractor.extract(audio_file)

        click.echo(f"\n파일: {Path(audio_file).name}")
        click.echo("-" * 40)

        for key, value in metadata.items():
            if value is not None:
                click.echo(f"{key}: {value}")

    except Exception as e:
        click.echo(f"오류: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
