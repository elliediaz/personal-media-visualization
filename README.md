# Personal Media Visualization

개인 미디어 파일(특히 음악)에 대한 포괄적인 분석 및 시각화 시스템입니다. 실시간 음악 재생, 고급 오디오 분석, 통계적/예술적 시각화, 외부 API 통합을 통해 미디어 아트 연구를 지원합니다.

## 주요 기능

### 1. 음악 재생
- 다양한 오디오 포맷 지원 (MP3, WAV, FLAC, OGG, M4A)
- 실시간 재생 제어 (재생, 일시정지, 정지, 탐색)
- 저지연 오디오 스트리밍
- 콜백 기반 오디오 프레임 접근

### 2. 오디오 분석 및 메타데이터 추출
- **스펙트럼 분석**: STFT, Mel-spectrogram, MFCC
- **리듬 분석**: 템포, 비트 추적, 음 시작점 감지
- **화성 분석**: 피치, 크로마, 키 감지
- **음색 분석**: 스펙트럼 중심, 롤오프, 제로 크로싱
- **메타데이터**: ID3 태그, 지속시간, 비트레이트

### 3. 시각화
#### 통계적 시각화
- 실시간 파형 디스플레이
- 스펙트로그램 (STFT, Mel)
- 주파수 스펙트럼 분석기
- 특성 타임라인 플롯
- 비트/음시작점 마커

#### 예술적 시각화
- 오디오 반응형 파티클 시스템
- 제너레이티브 아트 패턴
- 쉐이더 기반 이펙트
- 프랙탈 시각화
- 커스텀 예술 알고리즘

#### 레트로/사이키델릭 시각화
- CRT 모니터 효과
- 프랙탈, 만화경, 터널 시각화
- 글리치 아트, ASCII 렌더러
- 매트릭스 레인 효과

#### 고급 3D/4D 시각화 (계획됨)
- 3D 스펙트로그램 (시간-주파수-진폭)
- 3D 오디오 공간 시각화
- 포인트 클라우드 렌더링
- 볼류메트릭 렌더링
- 4차원 시각화 (3D + 시간/색상)

### 4. 데스크톱 GUI (메인프레임 스타일)
- 80~90년대 군사용 메인프레임/터미널 스타일 레트로 GUI
- CRT 인광 효과, 스캔라인, 노이즈, 비네트
- 52개 시각화 스타일 지원
- 다양한 오디오 입력 지원 (파일, 마이크, 시스템 루프백)
- 4가지 인광체 색상 (Green, Amber, White, Blue)

### 5. 외부 API 연동
- REST API 엔드포인트
- WebSocket 실시간 스트리밍
- 분석 데이터 제공
- 시각화 렌더링 서비스

## 빠른 시작

### 실행 스크립트 사용 (권장)

```bash
# Linux/macOS
./run.sh              # API 서버 시작
./run.sh dev          # 개발 모드 (자동 리로드)
./run.sh test         # 테스트 실행
./run.sh help         # 도움말

# Windows CMD
run.bat               # API 서버 시작
run.bat dev           # 개발 모드
run.bat test          # 테스트 실행
run.bat help          # 도움말

# Windows PowerShell
.\run.ps1             # API 서버 시작
.\run.ps1 dev         # 개발 모드
.\run.ps1 test        # 테스트 실행
.\run.ps1 help        # 도움말
```

서버 시작 후 접속:
- 웹 인터페이스: http://localhost:8000/web
- API 문서 (Swagger): http://localhost:8000/docs
- API 문서 (ReDoc): http://localhost:8000/redoc

### 데스크톱 GUI 실행

```bash
# Windows CMD
gui.bat                    # 기본 실행 (그린 인광체)
gui.bat amber              # 앰버 인광체
gui.bat -p blue --no-crt   # 블루, CRT 효과 없이

# 또는 Python 직접 실행
python run_gui.py -p green
```

**GUI 단축키:**
| 키 | 기능 |
|-----|------|
| F1/F2, LEFT/RIGHT | 시각화 전환 (52개 스타일) |
| F3 | CRT 효과 토글 |
| F4 | 인광체 색상 변경 |
| F5 | 설정 화면 (오디오 입력 선택) |
| SPACE | 재생/일시정지 (파일 모드) |
| ESC | 종료 |

### 실행 스크립트 명령어

| 명령어 | 설명 |
|--------|------|
| `server` | API 서버 시작 (기본값) |
| `dev` | 개발 모드로 서버 시작 (자동 리로드) |
| `test` | 테스트 실행 |
| `lint` | 코드 품질 검사 (ruff, black --check) |
| `format` | 코드 포매팅 (black, ruff --fix) |
| `check` | 전체 검사 (lint + type check) |
| `install` | 의존성 설치 |
| `install-dev` | 개발 의존성 설치 |
| `build` | 프로젝트 빌드/패키징 |
| `clean` | 캐시 및 임시 파일 정리 |
| `docs` | 문서 생성 |
| `benchmark` | 벤치마크 실행 |
| `coverage` | 커버리지 리포트 생성 |
| `info` | 시스템 정보 출력 |
| `help` | 도움말 표시 |

## 설치 방법

### 요구사항
- Python 3.10 이상
- pip 또는 poetry
- (선택) CUDA (GPU 가속)

### 설치

```bash
# 저장소 클론
git clone https://github.com/yourusername/personal-media-visualization.git
cd personal-media-visualization

# 가상 환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 개발 의존성 설치 (개발자용)
pip install -r requirements-dev.txt
```

또는 실행 스크립트 사용:

```bash
# Linux/macOS
./run.sh install       # 의존성 설치
./run.sh install-dev   # 개발 의존성 설치

# Windows
run.bat install        # 의존성 설치
run.bat install-dev    # 개발 의존성 설치
```

## 사용 방법

### CLI 인터페이스

```bash
# 기본 재생
python -m src.cli play audio.mp3

# 분석 수행
python -m src.cli analyze audio.mp3 --output analysis.json

# 시각화 생성
python -m src.cli visualize audio.mp3 --type spectrogram --output viz.png

# 배치 처리
python -m src.cli batch process ./audio_files/ --visualizers all
```

### Python API

```python
from src.audio.player import AudioPlayer
from src.analysis.extractor import FeatureExtractor
from src.visualization.statistical import SpectrogramVisualizer

# 오디오 재생
player = AudioPlayer("audio.mp3")
player.play()

# 특성 추출
extractor = FeatureExtractor()
features = extractor.extract("audio.mp3")

# 시각화
visualizer = SpectrogramVisualizer()
visualizer.render(features, output="spectrogram.png")
```

### REST API 서버

```bash
# API 서버 시작
python run_api_server.py

# 또는 실행 스크립트 사용
./run.sh        # Linux/macOS
run.bat         # Windows CMD
.\run.ps1       # Windows PowerShell
```

**API 엔드포인트:**

- `/api/v1/audio/upload` - 오디오 업로드
- `/api/v1/analysis/analyze` - 분석 요청
- `/api/v1/visualize/render` - 시각화 렌더링
- `/ws/audio/{audio_id}` - 오디오 스트림 (WebSocket)
- `/ws/features/{audio_id}` - 특성 스트림 (WebSocket)

## 프로젝트 구조

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
│   ├── gui/               # 데스크톱 GUI (메인프레임 스타일)
│   │   ├── mainframe_app.py  # 메인 애플리케이션
│   │   ├── visualizations.py # 52개 시각화 스타일
│   │   └── audio_input.py    # 오디오 입력 관리
│   ├── api/               # REST API 및 WebSocket
│   ├── cli/               # CLI 인터페이스
│   └── utils/             # 유틸리티 함수
├── tests/                 # 테스트
│   ├── unit/              # 단위 테스트
│   ├── integration/       # 통합 테스트
│   └── benchmarks/        # 벤치마크
├── docs/                  # 문서
├── data/                  # 데이터 (샘플, 캐시)
├── output/                # 출력 (렌더링, 내보내기)
├── config/                # 설정 파일
├── static/                # 정적 파일 (CSS, JS)
├── templates/             # HTML 템플릿
├── run.sh                 # Linux/macOS 실행 스크립트
├── run.bat                # Windows CMD 실행 스크립트
├── run.ps1                # Windows PowerShell 실행 스크립트
├── gui.bat                # GUI 실행 스크립트 (Windows)
├── run_gui.py             # GUI 진입점
└── run_api_server.py      # API 서버 진입점
```

## 설정

설정 파일은 `config/` 디렉토리에 있습니다:

- `default.yaml`: 기본 설정

환경 변수를 통해 설정을 재정의할 수 있습니다:

```bash
export PMV_AUDIO_SAMPLE_RATE=48000
export PMV_API_PORT=8080
```

실행 스크립트에서 사용할 수 있는 환경 변수:

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `PMV_HOST` | 서버 호스트 | 0.0.0.0 |
| `PMV_PORT` | 서버 포트 | 8000 |
| `PYTHON` | Python 실행 파일 | python3/python |

## 개발

### 개발 환경 설정

```bash
# pre-commit 훅 설치
pre-commit install

# 코드 포매팅
./run.sh format    # 또는 run.bat format

# 코드 품질 검사
./run.sh lint      # 또는 run.bat lint

# 전체 검사 (lint + type check)
./run.sh check     # 또는 run.bat check
```

### 테스트

```bash
# 모든 테스트 실행
./run.sh test

# 커버리지 리포트
./run.sh coverage

# 특정 테스트만 실행
./run.sh test -k player

# 벤치마크
./run.sh benchmark
```

## 개발 단계

프로젝트는 7개의 단계로 나누어 개발됩니다:

- [x] Phase 1: 기초 및 기본 재생
- [x] Phase 2: 오디오 분석
- [x] Phase 3: 통계적 시각화
- [x] Phase 4: 예술적 시각화
- [x] Phase 5: API 통합
- [x] Phase 5.5: 웹 인터페이스, CLI 완성, 레트로/사이키델릭 시각화
- [ ] Phase 6: 3D/4D 시각화
- [ ] Phase 7: 최종 통합 및 최적화

## 성능 최적화

### 라즈베리파이 지원
실행 스크립트는 라즈베리파이 환경을 자동으로 감지하여 최적화 모드를 적용합니다.

### 성능 목표
- 오디오 지연: <50ms
- 시각화 FPS: 60 FPS (2D), 30-60 FPS (3D)
- 특성 추출: 표준 특성에 대해 실시간
- API 응답 시간: <100ms (처리 시간 제외)

## 라이선스

MIT License

## 감사의 말

이 프로젝트는 다음 오픈소스 라이브러리들을 사용합니다:
- librosa
- essentia
- pygame
- FastAPI
- 그 외 많은 훌륭한 라이브러리들
