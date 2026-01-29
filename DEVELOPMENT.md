# 개발 가이드

이 문서는 Personal Media Visualization 프로젝트의 개발 가이드입니다.

## 프로젝트 개요

Python 기반의 오디오 분석 및 시각화 시스템으로, 미디어 아트 연구를 위한 도구입니다.
실시간 음악 재생, 고급 오디오 분석, 통계적/예술적 시각화, REST API/WebSocket 통합을 제공합니다.

**현재 상태**: Phase 1-5.5 완료 (재생, 분석, 통계적 시각화, 예술적 시각화, API, 웹 인터페이스, 레트로/사이키델릭 시각화). Phase 6 (3D/4D 시각화)과 Phase 7 (통합)은 진행 예정.

## 실행 스크립트

프로젝트는 세 가지 실행 스크립트를 제공합니다:
- `run.sh` - Linux/macOS용 Bash 스크립트
- `run.bat` - Windows CMD용 배치 스크립트
- `run.ps1` - Windows PowerShell용 스크립트

### 사용 가능한 명령어

| 명령어 | 설명 |
|--------|------|
| `server` | API 서버 시작 (기본값) |
| `dev` | 개발 모드로 서버 시작 (자동 리로드) |
| `test` | 테스트 실행 (pytest) |
| `lint` | 코드 품질 검사 (ruff, black --check) |
| `format` | 코드 포매팅 (black, ruff --fix) |
| `check` | 전체 검사 (lint + mypy) |
| `install` | 의존성 설치 |
| `install-dev` | 개발 의존성 설치 |
| `build` | 프로젝트 빌드/패키징 |
| `clean` | 캐시 및 임시 파일 정리 |
| `docs` | 문서 생성 |
| `benchmark` | 벤치마크 실행 |
| `coverage` | 커버리지 리포트 생성 |
| `info` | 시스템 정보 출력 |
| `help` | 도움말 표시 |

### 예시

```bash
# Linux/macOS
./run.sh                    # 서버 시작
./run.sh dev                # 개발 모드
./run.sh test -k player     # 'player' 키워드 테스트만 실행
PMV_PORT=9000 ./run.sh      # 포트 9000에서 시작

# Windows CMD
run.bat                     # 서버 시작
run.bat dev                 # 개발 모드
run.bat test -k player      # 'player' 키워드 테스트만 실행
set PMV_PORT=9000 && run.bat # 포트 9000에서 시작

# Windows PowerShell
.\run.ps1                   # 서버 시작
.\run.ps1 dev               # 개발 모드
.\run.ps1 test -k player    # 'player' 키워드 테스트만 실행
$env:PMV_PORT=9000; .\run.ps1 # 포트 9000에서 시작
```

## 주요 명령어

```bash
# 의존성 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 개발용

# 또는 실행 스크립트 사용
./run.sh install       # Linux/macOS
./run.sh install-dev   # Linux/macOS 개발 의존성
run.bat install        # Windows

# 테스트
./run.sh test                         # 전체 테스트
./run.sh test -k player               # 특정 테스트
./run.sh test tests/unit/test_player.py # 단일 파일
./run.sh coverage                     # 커버리지 포함

# 코드 품질
./run.sh format        # 코드 포매팅 (black, ruff --fix)
./run.sh lint          # 코드 품질 검사 (black --check, ruff)
./run.sh check         # 전체 검사 (lint + mypy)

# 정리
./run.sh clean         # 캐시 및 임시 파일 정리

# API 서버
./run.sh               # http://localhost:8000 시작
./run.sh dev           # 개발 모드 (자동 리로드)
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
- **`src/visualization/retro/`**: CRT 효과, 레트로 색상 팔레트, 사이키델릭 시각화 (프랙탈, 만화경, 터널), 실험적 효과 (글리치, ASCII, 매트릭스).
- **`src/visualization/animation/`**: 애니메이션 엔진, GIF/MP4 내보내기.
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

## 모듈 Import

프로젝트의 모든 모듈은 적절한 `__init__.py`를 통해 공개 API가 정의되어 있습니다:

```python
# 버전 정보
from src import __version__

# 분석 모듈
from src.analysis import FeatureExtractor, AnalysisResult

# 오디오 모듈
from src.audio import AudioPlayer, PlayerState, AudioFormat

# 시각화 모듈
from src.visualization import BaseVisualizer
from src.visualization.statistical import SpectrogramVisualizer, WaveformVisualizer
from src.visualization.artistic import ParticleVisualizer, ColorMapper
from src.visualization.retro import CRTProcessor
from src.visualization.animation import AnimationEngine, GIFExporter

# 핵심 모듈
from src.core import config, PMVException

# 유틸리티
from src.utils import get_logger, PerformanceMonitor

# API
from src.api import app
```

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
│   │   ├── retro/         # 레트로/CRT 효과
│   │   ├── animation/     # 애니메이션 및 내보내기
│   │   └── advanced/      # 3D/4D 시각화 (예정)
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
├── run.bat                # Windows CMD 실행 스크립트
├── run.ps1                # Windows PowerShell 실행 스크립트
└── run_api_server.py      # API 서버 진입점
```

## 개발 워크플로우

1. 기능 브랜치 생성
2. 코드 작성 및 테스트
3. 코드 포매팅 (`./run.sh format`)
4. 코드 품질 검사 (`./run.sh check`)
5. 테스트 통과 확인 (`./run.sh test`)
6. 커밋 및 PR 생성

### 커밋 메시지 형식

```
타입: 간단한 설명

상세 설명 (필요시)

관련 이슈: #123
```

**타입:**
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅
- `perf`: 성능 개선
- `chore`: 기타 변경사항

## 크로스 플랫폼 지원

- Linux, macOS, Windows 지원
- `run.sh` (Linux/macOS), `run.bat` (Windows CMD), `run.ps1` (Windows PowerShell) 실행 스크립트 제공
- 라즈베리파이 환경 자동 감지 및 최적화
- WSL (Windows Subsystem for Linux) 환경 지원
- 경로 처리에 `pathlib.Path` 사용으로 플랫폼 독립적

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `PMV_HOST` | 서버 호스트 | 0.0.0.0 |
| `PMV_PORT` | 서버 포트 | 8000 |
| `PYTHON` | Python 실행 파일 | python3 (Linux/macOS), python (Windows) |
| `PMV_PERFORMANCE_MODE` | 성능 모드 (low/medium/high) | auto |
| `PMV_AUDIO_SAMPLE_RATE` | 오디오 샘플레이트 | 22050 |
| `PMV_API_*` | API 관련 설정 | - |
