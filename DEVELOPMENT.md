# 개발 가이드

이 문서는 Personal Media Visualization 프로젝트의 개발 가이드입니다.

## 프로젝트 개요

Python 기반의 오디오 분석 및 시각화 시스템으로, 미디어 아트 연구를 위한 도구입니다.
실시간 음악 재생, 고급 오디오 분석, 통계적/예술적 시각화, REST API/WebSocket 통합을 제공합니다.

**현재 상태**: Phase 1-5 완료 (재생, 분석, 통계적 시각화, 예술적 시각화, API). Phase 6 (3D/4D 시각화)과 Phase 7 (통합)은 진행 예정.

## 주요 명령어

```bash
# 의존성 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 개발용

# 실행 스크립트 사용
./run.sh              # API 서버 시작
./run.sh dev          # 개발 모드 (자동 리로드)
./run.sh test         # 테스트 실행
./run.sh lint         # 코드 품질 검사

# 테스트
pytest                                    # 전체 테스트 (커버리지 포함)
pytest tests/unit/test_player.py          # 단일 테스트 파일
pytest -m "not slow"                      # 느린 테스트 제외
pytest tests/benchmarks/ --benchmark-only # 벤치마크만

# 코드 품질
black src tests                           # 코드 포매팅
ruff check src tests                      # 린팅
mypy src                                  # 타입 체크
pre-commit install && pre-commit run --all-files

# API 서버
python run_api_server.py                  # http://localhost:8000 시작
# Swagger: /docs, ReDoc: /redoc

# CLI 사용
python -m src.cli play audio.mp3
python -m src.cli analyze audio.mp3 --output analysis.json
python -m src.cli visualize audio.mp3 --type spectrogram --output viz.png
python -m src.cli serve --port 8000       # API 서버 시작
```

## 아키텍처

### 핵심 컴포넌트

- **`src/core/config.py`**: 싱글톤 설정 관리. `config/default.yaml` 사용. 점 표기법 지원 (`config.get("audio.sample_rate")`), 환경 변수 오버라이드 (`PMV_AUDIO_SAMPLE_RATE`).
- **`src/core/exceptions.py`**: 오디오, 설정, 시각화 관련 커스텀 예외 계층.

### 오디오 파이프라인

- **`src/audio/player.py`**: `AudioPlayer` 클래스. pygame.mixer 기반 재생, 상태 머신 (STOPPED/PLAYING/PAUSED), 콜백 지원, librosa 통합.
- **`src/audio/formats.py`**: MP3, WAV, FLAC, OGG, M4A 포맷 감지 및 검증.

### 분석 시스템

- **`src/analysis/extractor.py`**: `FeatureExtractor`가 모든 분석기를 조율 (스펙트럼, 리듬, 화성, 음색) 및 메타데이터 추출.
- `src/analysis/` 내 개별 분석기: `spectral.py` (STFT, Mel, MFCC), `rhythm.py` (템포, 비트), `harmony.py` (피치, 크로마, 키), `timbre.py` (스펙트럼 특성).
- **`src/analysis/result.py`**: 추출된 모든 특성을 포함하는 `AnalysisResult` 데이터클래스.
- **`src/analysis/cache.py`**: 분석 결과 캐싱.

### 시각화 시스템

- **`src/visualization/base.py`**: `BaseVisualizer` 추상 클래스 - 모든 시각화기가 상속. matplotlib Figure 관리, 색상 테마, save/show 메서드 제공.
- **`src/visualization/statistical/`**: 파형, 스펙트로그램, 스펙트럼, 특성 타임라인, 리듬 시각화기.
- **`src/visualization/artistic/`**: 파티클 시스템, 제너레이티브 패턴, 색상 매핑. `BaseArtisticVisualizer` 사용.
- **`src/visualization/advanced/`**: 3D/4D 시각화 예정 (Phase 6).

### API 계층

- **`src/api/app.py`**: FastAPI 애플리케이션. CORS, 로깅 미들웨어, 예외 핸들러, 생명주기 관리, 정적 파일 서빙.
- **`src/api/routes/`**: REST 엔드포인트 - `audio.py` (업로드), `analysis.py` (분석), `visualization.py` (렌더링).
- **`src/api/websocket.py`**: 오디오 및 특성 실시간 스트리밍.
- **`src/api/models.py`**: 요청/응답 검증용 Pydantic 모델.

### CLI 인터페이스

- **`src/cli/main.py`**: click 기반 명령행 인터페이스. play, analyze, visualize, batch, serve, info 명령 제공.

### 웹 인터페이스

- **`templates/index.html`**: 메인 웹 페이지 (Jinja2 템플릿).
- **`static/css/style.css`**: 스타일시트 (다크 테마).
- **`static/js/app.js`**: 프론트엔드 JavaScript 애플리케이션.

## 주요 패턴

- **설정**: `from src.core.config import config` 싱글톤 사용. 생성자에서 `config_override` 딕셔너리로 오버라이드 가능.
- **로깅**: `from src.utils.logging import get_logger; logger = get_logger(__name__)` 사용.
- **시각화 패턴**: `BaseVisualizer` 상속, `render()` 구현, matplotlib 설정에 `create_figure()` 사용.
- **분석 패턴**: 분석기는 `(audio_data, sample_rate)` numpy 배열을 받아 특성 딕셔너리 반환.

## 기술 스택

- **오디오**: librosa (분석), pygame (재생), soundfile/pydub (I/O), mutagen (메타데이터)
- **시각화**: matplotlib/seaborn (통계적), plotly (인터랙티브), vispy/moderngl (OpenGL 3D)
- **API**: FastAPI + uvicorn, Pydantic v2, WebSockets, Jinja2
- **테스트**: pytest with pytest-cov, pytest-asyncio, pytest-benchmark

## 설정

설정은 `config/default.yaml`에 정의. 주요 섹션: `audio` (sample_rate, buffer_size), `analysis` (frame_size, hop_size), `visualization` (fps, resolution, colors), `api` (host, port, CORS).

환경 변수로 오버라이드: `PMV_<섹션>_<키>` (예: `PMV_API_PORT=8080`).

## 디렉토리 구조

```
personal-media-visualization/
├── src/
│   ├── core/              # 핵심 시스템 (설정, 예외, 로깅)
│   ├── audio/             # 오디오 재생 및 I/O
│   ├── analysis/          # 오디오 분석 및 특성 추출
│   ├── visualization/     # 시각화 모듈
│   │   ├── statistical/   # 통계적 시각화
│   │   ├── artistic/      # 예술적 시각화
│   │   └── advanced/      # 3D/4D 시각화
│   ├── api/               # REST API 및 WebSocket
│   ├── cli/               # CLI 인터페이스
│   └── utils/             # 유틸리티 함수
├── tests/                 # 테스트
├── docs/                  # 문서
├── data/                  # 데이터 (업로드, 캐시)
├── output/                # 출력 (렌더링, 내보내기)
├── config/                # 설정 파일
├── static/                # 정적 파일 (CSS, JS)
├── templates/             # HTML 템플릿
├── run.sh                 # Linux/macOS 실행 스크립트
├── run.bat                # Windows 실행 스크립트
└── run_api_server.py      # API 서버 진입점
```

## 개발 워크플로우

1. 기능 브랜치 생성
2. 코드 작성 및 테스트
3. `black`과 `ruff`로 코드 품질 확인
4. 테스트 통과 확인 (`pytest`)
5. 커밋 및 PR 생성

## 크로스 플랫폼 지원

- Linux, macOS, Windows 지원
- `run.sh` (Linux/macOS) 및 `run.bat` (Windows) 실행 스크립트 제공
- 경로 처리에 `pathlib.Path` 사용으로 플랫폼 독립적
