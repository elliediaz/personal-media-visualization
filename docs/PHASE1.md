# Phase 1: 기초 및 기본 재생

## 목표

프로젝트의 기본 구조를 확립하고 기본적인 오디오 재생 기능을 구현합니다.

## 완료된 작업

### 1. 프로젝트 구조 설정
- [x] 디렉토리 구조 생성
- [x] Git 설정 (사용자 정보)
- [x] .gitignore 설정
- [x] README.md 작성
- [x] CLAUDE.MD 작성 (개발 가이드)

### 2. 의존성 관리
- [x] requirements.txt 생성
- [x] requirements-dev.txt 생성
- [x] pyproject.toml 설정

### 3. 설정 시스템
- [x] config/default.yaml 생성
- [x] src/core/config.py 구현
- [x] 환경 변수 지원

### 4. 핵심 모듈
- [x] src/core/exceptions.py (예외 클래스)
- [x] src/utils/logging.py (로깅 시스템)

## 다음 단계

### 5. 오디오 파일 형식 지원
- [ ] src/audio/formats.py
  - [ ] AudioFormat enum
  - [ ] 포맷 감지 함수
  - [ ] 포맷 변환 유틸리티

### 6. 오디오 플레이어 구현
- [ ] src/audio/player.py
  - [ ] AudioPlayer 클래스
  - [ ] 파일 로드
  - [ ] 재생 제어 (play, pause, stop, seek)
  - [ ] 볼륨 제어
  - [ ] 콜백 시스템

### 7. 테스트
- [ ] tests/unit/test_config.py
- [ ] tests/unit/test_player.py
- [ ] tests/unit/test_formats.py

### 8. 문서화
- [ ] API 문서 시작
- [ ] 사용 예제

## 사용할 프롬프트

```
Continue implementing Phase 1 of the Personal Media Visualization project.

Tasks to complete:

1. Implement src/audio/formats.py:
   - Create AudioFormat enum with supported formats (MP3, WAV, FLAC, OGG, M4A)
   - Add format detection function from file extension and magic bytes
   - Include format metadata (description, supported codecs)

2. Implement src/audio/player.py:
   - Create AudioPlayer class using pygame.mixer
   - Methods: load(), play(), pause(), stop(), seek()
   - Properties: duration, position, volume, is_playing
   - Callback system for audio events (on_play, on_pause, on_stop, on_end)
   - Real-time audio data access for visualization

3. Add unit tests:
   - Test configuration loading
   - Test audio format detection
   - Mock-based tests for audio player

Requirements:
- All docstrings and comments in Korean
- Type hints for all functions
- Comprehensive error handling
- Follow PEP 8 style guide
```

## 기술 사양

### AudioFormat (src/audio/formats.py)
```python
class AudioFormat(Enum):
    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    OGG = "ogg"
    M4A = "m4a"
    AAC = "aac"

def detect_format(file_path: Path) -> AudioFormat
def get_format_info(format: AudioFormat) -> dict
```

### AudioPlayer (src/audio/player.py)
```python
class AudioPlayer:
    def __init__(self, config: Config = None)
    def load(self, file_path: Path) -> None
    def play(self) -> None
    def pause(self) -> None
    def stop(self) -> None
    def seek(self, position: float) -> None

    @property
    def duration(self) -> float

    @property
    def position(self) -> float

    @property
    def volume(self) -> float

    @volume.setter
    def volume(self, value: float) -> None

    @property
    def is_playing(self) -> bool
```

## 테스트 계획

### 단위 테스트
1. **Config 테스트**
   - 설정 파일 로드
   - 점 표기법 접근
   - 환경 변수 우선순위
   - 깊은 업데이트

2. **AudioFormat 테스트**
   - 확장자 기반 감지
   - 잘못된 형식 처리
   - 포맷 정보 조회

3. **AudioPlayer 테스트** (Mock 사용)
   - 파일 로드
   - 재생 제어
   - 볼륨 제어
   - 이벤트 콜백

### 통합 테스트
- 실제 오디오 파일로 재생 테스트 (샘플 파일 필요)

## 예상 이슈 및 해결

### 이슈 1: pygame 초기화
**문제**: pygame.mixer 초기화 시 설정 필요

**해결**:
```python
pygame.mixer.init(
    frequency=config.get("audio.sample_rate"),
    size=-16,
    channels=2,
    buffer=config.get("audio.buffer_size")
)
```

### 이슈 2: 오디오 데이터 접근
**문제**: pygame.mixer는 raw 오디오 데이터 직접 접근 어려움

**해결**:
- Phase 1에서는 기본 재생만 구현
- Phase 2에서 librosa/soundfile로 데이터 추출

### 이슈 3: 크로스 플랫폼 호환성
**문제**: 오디오 백엔드가 OS마다 다름

**해결**:
- 설정 파일에서 백엔드 선택 가능하도록
- 테스트 시 다양한 환경 고려

## 성능 목표

- 오디오 파일 로드: <1초 (일반 크기 파일)
- 재생 시작 지연: <100ms
- 메모리 사용: <50MB (재생 시)

## 다음 Phase로의 연결

Phase 1이 완료되면:
- Phase 2에서 오디오 분석 기능 추가
- AudioPlayer에 분석 데이터 제공 기능 통합
- 실시간 오디오 스트림 접근 개선
