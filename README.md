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

#### 고급 3D/4D 시각화
- 3D 스펙트로그램 (시간-주파수-진폭)
- 3D 오디오 공간 시각화
- 포인트 클라우드 렌더링
- 볼류메트릭 렌더링
- 4차원 시각화 (3D + 시간/색상)

### 4. 외부 API 연동
- REST API 엔드포인트
- WebSocket 실시간 스트리밍
- 분석 데이터 제공
- 시각화 렌더링 서비스

### 5. 연구 및 실험
- 3D/4D 시각화 기법 탐구
- 미디어 아트 알고리즘 연구
- 맞춤형 시각화 개발
- VR/AR 지원 (선택사항)

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
│   │   └── advanced/      # 3D/4D 시각화
│   ├── api/               # REST API 및 WebSocket
│   └── utils/             # 유틸리티 함수
├── tests/                 # 테스트
│   ├── unit/              # 단위 테스트
│   └── integration/       # 통합 테스트
├── docs/                  # 문서
├── data/                  # 데이터 (샘플, 캐시)
├── output/                # 출력 (렌더링, 내보내기)
├── config/                # 설정 파일
└── scripts/               # 유틸리티 스크립트
```

## 기술 스택

### 오디오 처리
- **librosa**: 오디오 분석 및 특성 추출
- **soundfile/pydub**: 오디오 I/O
- **pygame/pyaudio**: 실시간 재생
- **essentia**: 고급 오디오 분석
- **aubio**: 비트 감지 및 피치 추적

### 시각화
- **matplotlib/seaborn**: 통계적 플롯
- **plotly**: 인터랙티브 시각화
- **pygame**: 실시간 2D 렌더링
- **vispy/moderngl**: OpenGL 기반 3D 시각화
- **Open3D**: 3D 포인트 클라우드

### API 및 통합
- **FastAPI**: REST API 서버
- **WebSockets**: 실시간 데이터 스트리밍
- **Redis**: 캐시 및 메시지 브로커

### 프론트엔드 (선택사항)
- **React + TypeScript**
- **Three.js**: 3D 웹 시각화
- **D3.js**: 데이터 기반 시각화

## 개발 단계

프로젝트는 7개의 단계로 나누어 개발됩니다:

1. **Phase 1**: 기초 및 기본 재생
2. **Phase 2**: 오디오 분석 및 메타데이터 추출
3. **Phase 3**: 통계적 시각화
4. **Phase 4**: 예술적 시각화
5. **Phase 5**: 외부 API 통합
6. **Phase 6**: 고급 3D/4D 시각화
7. **Phase 7**: 통합 및 최적화

각 단계는 독립적으로 개발, 테스트, 커밋되며 최종적으로 하나의 통합 솔루션으로 합쳐집니다.

## 빠른 시작

### 실행 스크립트 사용 (권장)

```bash
# Linux/macOS
./run.sh              # API 서버 시작
./run.sh dev          # 개발 모드 (자동 리로드)
./run.sh test         # 테스트 실행
./run.sh help         # 도움말

# Windows
run.bat               # API 서버 시작
run.bat dev           # 개발 모드
run.bat test          # 테스트 실행
run.bat help          # 도움말
```

서버 시작 후 접속:
- 웹 인터페이스: http://localhost:8000/web
- API 문서 (Swagger): http://localhost:8000/docs
- API 문서 (ReDoc): http://localhost:8000/redoc

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

### 개발 환경 설정

```bash
# pre-commit 훅 설치
pre-commit install

# 테스트 실행
pytest

# 코드 포맷팅
black src tests
ruff check src tests
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

# API 문서 확인
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

**API 엔드포인트:**

- `/api/v1/audio/upload` - 오디오 업로드
- `/api/v1/analysis/analyze` - 분석 요청
- `/api/v1/visualize/render` - 시각화 렌더링
- `/ws/audio/{audio_id}` - 오디오 스트림 (WebSocket)
- `/ws/features/{audio_id}` - 특성 스트림 (WebSocket)

**Python 클라이언트 예제:**

```python
from pathlib import Path
from docs.examples.api_client_examples import AudioVisualizationClient

with AudioVisualizationClient() as client:
    # 오디오 업로드
    result = client.upload_audio(Path("audio.mp3"))
    audio_id = result["audio_id"]

    # 분석 요청
    analysis = client.analyze_audio(audio_id)
    completed = client.wait_for_analysis(analysis["analysis_id"])

    # 시각화 렌더링
    viz = client.render_visualization(
        viz_type="particles",
        analysis_id=completed["analysis_id"],
        params={"num_particles": 3000}
    )

    # 다운로드
    client.download_visualization(viz["viz_id"], Path("output.png"))
```

## 설정

설정 파일은 `config/` 디렉토리에 있습니다:

- `default.yaml`: 기본 설정
- `audio.yaml`: 오디오 관련 설정
- `visualization.yaml`: 시각화 설정
- `api.yaml`: API 서버 설정

환경 변수를 통해 설정을 재정의할 수 있습니다:

```bash
export PMV_AUDIO_SAMPLE_RATE=48000
export PMV_API_PORT=8080
```

## 테스트

```bash
# 모든 테스트 실행
pytest

# 커버리지 포함
pytest --cov=src --cov-report=html

# 특정 테스트만 실행
pytest tests/unit/test_player.py

# 성능 벤치마크
pytest tests/benchmarks/ --benchmark-only
```

## 기여 가이드라인

### 코드 스타일
- PEP 8 준수
- 모든 함수에 타입 힌트 사용
- 한글로 된 docstring (Google 스타일)
- `black`으로 포맷팅
- `ruff`로 린팅

### 커밋 메시지
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

### Pull Request
1. Feature 브랜치 생성
2. 변경사항 커밋
3. 테스트 추가/업데이트
4. Pull Request 생성
5. 코드 리뷰 대기

## 성능 목표

### 실시간 처리
- 오디오 지연: <50ms
- 시각화 FPS: 60 FPS (2D), 30-60 FPS (3D)
- 특성 추출: 표준 특성에 대해 실시간
- API 응답 시간: <100ms (처리 시간 제외)

### 리소스 사용
- 메모리: 일반 사용 시 <2GB
- CPU: 현대적인 쿼드코어에서 <50%
- GPU: 사용 가능한 VRAM의 효율적 사용

## 라이선스

MIT License

## 문의

프로젝트 관련 문의사항은 이슈를 통해 남겨주세요.

## 감사의 말

이 프로젝트는 다음 오픈소스 라이브러리들을 사용합니다:
- librosa
- essentia
- pygame
- FastAPI
- 그 외 많은 훌륭한 라이브러리들

## 로드맵

- [x] Phase 1: 기초 및 기본 재생
- [x] Phase 2: 오디오 분석
- [x] Phase 3: 통계적 시각화
- [x] Phase 4: 예술적 시각화
- [x] Phase 5: API 통합
- [x] Phase 5.5: 웹 인터페이스 및 CLI 완성
- [ ] Phase 6: 3D/4D 시각화
- [ ] Phase 7: 최종 통합 및 최적화
- [ ] 머신러닝 기반 분류
- [ ] 모바일 앱 통합
- [ ] VR/AR 지원
