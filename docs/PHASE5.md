# Phase 5: API Integration

외부 프로그램 연동을 위한 REST API 및 WebSocket 서버 구현

## 개요

Phase 5에서는 오디오 분석 및 시각화 기능을 외부 프로그램에서 활용할 수 있도록 FastAPI 기반의 REST API와 WebSocket 실시간 스트리밍을 구현했습니다.

## 구현된 기능

### 1. API 모델 (Pydantic)

**파일:** `src/api/models.py`

- 요청/응답 모델 정의
- 데이터 검증 및 직렬화
- Enum 타입 정의

**주요 모델:**
- `AudioUploadRequest/Response`: 오디오 업로드
- `AnalysisRequest/Response`: 분석 요청/결과
- `VisualizationRequest/Response`: 시각화 렌더링
- `StreamMessage`: WebSocket 메시지
- `FeatureData`: 특성 요약

### 2. FastAPI 애플리케이션

**파일:** `src/api/app.py`

**기능:**
- CORS 설정
- 요청 로깅 미들웨어
- 예외 핸들러 (검증 에러, 서버 에러)
- 헬스체크 엔드포인트
- 생명주기 관리 (lifespan)
- 라우터 자동 등록

**미들웨어:**
- 요청/응답 시간 로깅
- 처리 시간 헤더 추가 (X-Process-Time)

### 3. REST API 엔드포인트

#### 오디오 API (`src/api/routes/audio.py`)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/audio/upload` | 오디오 파일 업로드 |
| GET | `/api/v1/audio/{audio_id}` | 오디오 정보 조회 |
| GET | `/api/v1/audio/{audio_id}/download` | 오디오 파일 다운로드 |
| DELETE | `/api/v1/audio/{audio_id}` | 오디오 삭제 |
| GET | `/api/v1/audio/` | 오디오 목록 조회 |

**특징:**
- 파일 크기 제한 (100MB)
- 포맷 검증
- UUID 기반 ID 생성
- 메타데이터 자동 추출

#### 분석 API (`src/api/routes/analysis.py`)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/analysis/analyze` | 분석 요청 |
| GET | `/api/v1/analysis/{analysis_id}` | 분석 결과 조회 |
| GET | `/api/v1/analysis/{analysis_id}/features` | 특성 데이터 조회 |
| DELETE | `/api/v1/analysis/{analysis_id}` | 분석 결과 삭제 |
| GET | `/api/v1/analysis/` | 분석 목록 조회 |

**특징:**
- 백그라운드 태스크로 비동기 분석
- 분석 상태 추적 (PENDING, PROCESSING, COMPLETED, FAILED)
- 특성 요약 자동 생성
- 선택적 특성 추출

#### 시각화 API (`src/api/routes/visualization.py`)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/visualize/render` | 시각화 렌더링 |
| GET | `/api/v1/visualize/{viz_id}` | 시각화 정보 조회 |
| GET | `/api/v1/visualize/{viz_id}/download` | 시각화 파일 다운로드 |
| DELETE | `/api/v1/visualize/{viz_id}` | 시각화 삭제 |
| GET | `/api/v1/visualize/presets` | 프리셋 목록 조회 |
| GET | `/api/v1/visualize/` | 시각화 목록 조회 |

**지원 시각화:**
- `waveform`: 파형
- `spectrogram`: 스펙트로그램
- `mel_spectrogram`: Mel 스펙트로그램
- `spectrum`: 스펙트럼
- `features`: 특성 타임라인
- `rhythm`: 리듬 분석
- `particles`: 파티클 시각화
- `circles`: 동심원
- `waves`: 파동 간섭

**프리셋:**
- 미리 정의된 시각화 설정
- 파라미터 템플릿 제공

### 4. WebSocket 실시간 스트리밍

**파일:** `src/api/websocket.py`

#### 엔드포인트

| 경로 | 설명 |
|------|------|
| `/ws/audio/{audio_id}` | 오디오 프레임 스트리밍 |
| `/ws/features/{audio_id}` | 특성 스트리밍 |
| `/ws/visualization/{audio_id}?viz_type=...` | 시각화 데이터 스트리밍 |

**기능:**
- ConnectionManager로 연결 관리
- 실시간 프레임 단위 전송
- 자동 프레임 레이트 조절
- 연결 해제 처리

**메시지 타입:**
- `audio`: 오디오 프레임
- `audio_end`: 오디오 스트림 종료
- `features`: 특성 프레임
- `features_end`: 특성 스트림 종료
- `visualization`: 시각화 데이터
- `visualization_end`: 시각화 스트림 종료

### 5. API 클라이언트 예제

**파일:** `docs/examples/api_client_examples.py`

**클래스:**
- `AudioVisualizationClient`: REST API 클라이언트
  - 오디오 업로드
  - 분석 요청 및 대기
  - 시각화 렌더링
  - 파일 다운로드
  - 프리셋 조회

**예제 함수:**
- `example_basic_workflow()`: 기본 워크플로우
- `example_presets()`: 프리셋 사용
- `example_websocket_audio_stream()`: 오디오 스트림
- `example_websocket_features()`: 특성 스트림

### 6. 서버 실행

**파일:** `run_api_server.py`

```bash
python run_api_server.py
```

**서버 접속:**
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 설정

### config/default.yaml

```yaml
api:
  version: "1.0.0"
  host: "0.0.0.0"
  port: 8000
  upload_dir: "data/uploads"
  output_dir: "output/api"
  max_upload_size: 104857600  # 100MB

  cors:
    enabled: true
    origins: ["*"]

  websocket:
    heartbeat_interval: 30
    max_connections: 100
```

## 사용 예제

### 1. REST API 사용

```python
from pathlib import Path
from docs.examples.api_client_examples import AudioVisualizationClient

with AudioVisualizationClient() as client:
    # 오디오 업로드
    result = client.upload_audio(Path("audio.mp3"))
    audio_id = result["audio_id"]

    # 분석 요청
    analysis = client.analyze_audio(audio_id)
    analysis_id = analysis["analysis_id"]

    # 분석 완료 대기
    completed = client.wait_for_analysis(analysis_id)

    # 시각화 렌더링
    viz = client.render_visualization(
        viz_type="particles",
        analysis_id=analysis_id,
        params={"num_particles": 3000}
    )

    # 다운로드
    client.download_visualization(viz["viz_id"], Path("output.png"))
```

### 2. WebSocket 사용

```python
import asyncio
import websockets

async def stream_features():
    uri = "ws://localhost:8000/ws/features/audio_id"

    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            if data["type"] == "features":
                print(f"Energy: {data['data']['energy']}")
            elif data["type"] == "features_end":
                break

asyncio.run(stream_features())
```

### 3. cURL 예제

```bash
# 헬스체크
curl http://localhost:8000/health

# 오디오 업로드
curl -X POST http://localhost:8000/api/v1/audio/upload \
  -F "file=@audio.mp3"

# 분석 요청
curl -X POST http://localhost:8000/api/v1/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{"audio_id": "uuid", "use_cache": true}'

# 프리셋 조회
curl http://localhost:8000/api/v1/visualize/presets
```

## 아키텍처

```
┌─────────────────┐
│  FastAPI App    │
│  (app.py)       │
└────────┬────────┘
         │
         ├──────────┐──────────┐
         │          │          │
    ┌────▼───┐ ┌───▼────┐ ┌──▼──────┐
    │ Audio  │ │Analysis│ │Visual   │
    │ Routes │ │ Routes │ │ Routes  │
    └────┬───┘ └───┬────┘ └──┬──────┘
         │          │          │
         └──────────┴──────────┘
                    │
         ┌──────────▼──────────┐
         │  Core Components    │
         │  - FeatureExtractor │
         │  - Visualizers      │
         │  - AudioPlayer      │
         └─────────────────────┘
```

## 테스트

```bash
# 서버 시작
python run_api_server.py

# 예제 실행
python docs/examples/api_client_examples.py
```

## 주요 기술

- **FastAPI**: 고성능 웹 프레임워크
- **Pydantic**: 데이터 검증
- **Uvicorn**: ASGI 서버
- **WebSockets**: 실시간 통신
- **httpx**: HTTP 클라이언트
- **BackgroundTasks**: 비동기 작업

## 다음 단계

Phase 6에서는 3D/4D 시각화 기능을 구현할 예정입니다.

## 참고

- FastAPI 문서: https://fastapi.tiangolo.com
- Pydantic 문서: https://docs.pydantic.dev
- WebSocket 프로토콜: https://websockets.readthedocs.io
