# Phase 2: 오디오 분석 및 메타데이터 추출

## 목표

오디오 파일로부터 다양한 특성을 추출하고 분석하여, 시각화를 위한 데이터를 생성합니다.

## 구현 계획

### 1. 특성 추출 시스템
- **FeatureExtractor 클래스** (src/analysis/extractor.py)
  - 실시간 특성 추출
  - 배치 처리 지원
  - 백엔드 선택 (librosa, essentia)
  - 진행률 콜백

### 2. 스펙트럼 분석
- **SpectralAnalyzer** (src/analysis/spectral.py)
  - STFT (Short-Time Fourier Transform)
  - Mel-spectrogram
  - MFCC (Mel-Frequency Cepstral Coefficients)
  - Spectral centroid, rolloff, bandwidth
  - Zero-crossing rate

### 3. 리듬 분석
- **RhythmAnalyzer** (src/analysis/rhythm.py)
  - 템포 감지 (BPM)
  - 비트 추적
  - Onset detection (음 시작점 감지)
  - Tempo curve (템포 변화 추적)

### 4. 화성 분석
- **HarmonicAnalyzer** (src/analysis/harmony.py)
  - 피치 추출
  - 크로마 특성 (Chroma features)
  - 키 감지 (Key detection)
  - 코드 추정 (Chord estimation)

### 5. 음색 분석
- **TimbreAnalyzer** (src/analysis/timbre.py)
  - Spectral contrast
  - Spectral flatness
  - Tonnetz (Tonal Centroid Features)
  - 음색 특성 벡터

### 6. 메타데이터 추출
- **MetadataExtractor** (src/analysis/metadata.py)
  - ID3 태그 (제목, 아티스트, 앨범 등)
  - 파일 정보 (크기, 지속시간, 비트레이트)
  - 커버 아트 추출
  - 정확한 오디오 길이 계산

### 7. 캐싱 시스템
- **AnalysisCache** (src/analysis/cache.py)
  - 해시 기반 캐싱
  - HDF5 저장 형식
  - TTL (Time-To-Live) 지원
  - 캐시 무효화

### 8. 분석 결과 데이터 클래스
- **AnalysisResult** (src/analysis/result.py)
  - 구조화된 특성 저장
  - JSON/CSV/HDF5 내보내기
  - 타임스탬프 정렬
  - 특성 접근 API

## 프롬프트

```
Implement Phase 2 of the Personal Media Visualization project: Audio Analysis and Metadata Extraction.

Tasks to complete:

1. Create FeatureExtractor class (src/analysis/extractor.py):
   - Load audio using librosa
   - Real-time and batch feature extraction
   - Progress callback system
   - Configurable parameters (frame_size, hop_size, sample_rate)

2. Implement SpectralAnalyzer (src/analysis/spectral.py):
   - STFT computation
   - Mel-spectrogram
   - MFCC extraction
   - Spectral features (centroid, rolloff, bandwidth, flatness)
   - Zero-crossing rate

3. Implement RhythmAnalyzer (src/analysis/rhythm.py):
   - Tempo detection (librosa.beat.tempo)
   - Beat tracking (librosa.beat.beat_track)
   - Onset detection (librosa.onset.onset_detect)
   - Tempo curve analysis

4. Implement HarmonicAnalyzer (src/analysis/harmony.py):
   - Pitch extraction (librosa.pyin)
   - Chroma features (librosa.feature.chroma_stft)
   - Key detection
   - Tonnetz features

5. Implement TimbreAnalyzer (src/analysis/timbre.py):
   - Spectral contrast
   - Spectral flatness
   - Additional timbre features

6. Implement MetadataExtractor (src/analysis/metadata.py):
   - ID3 tag extraction using mutagen
   - Audio file info (duration, bitrate, sample rate)
   - Cover art extraction
   - File hash computation

7. Implement AnalysisCache (src/analysis/cache.py):
   - File hash-based caching
   - Save/load using pickle or HDF5
   - TTL management
   - Cache cleanup

8. Create AnalysisResult data class (src/analysis/result.py):
   - Dataclass for structured storage
   - Export methods (to_json, to_csv, to_hdf5)
   - Feature access properties
   - Timestamp alignment utilities

9. Add comprehensive tests:
   - Unit tests for each analyzer
   - Integration tests with real audio
   - Cache functionality tests
   - Performance benchmarks

10. Update AudioPlayer integration:
    - Add get_duration() using librosa
    - Provide audio data access for real-time analysis

Requirements:
- All docstrings and comments in Korean
- Type hints for all functions
- Async support where beneficial
- Memory-efficient processing
- Comprehensive error handling
- Progress tracking for long operations
```

## 기술 사양

### FeatureExtractor
```python
class FeatureExtractor:
    def __init__(self, config: dict = None)
    def extract(self, file_path: Path, features: list[str] = None) -> AnalysisResult
    def extract_realtime(self, audio_data: np.ndarray, sr: int) -> AnalysisResult
    async def extract_async(self, file_path: Path) -> AnalysisResult
```

### SpectralAnalyzer
```python
class SpectralAnalyzer:
    def compute_stft(self, y: np.ndarray, sr: int) -> np.ndarray
    def compute_mel_spectrogram(self, y: np.ndarray, sr: int) -> np.ndarray
    def compute_mfcc(self, y: np.ndarray, sr: int) -> np.ndarray
    def compute_spectral_features(self, y: np.ndarray, sr: int) -> dict
```

### RhythmAnalyzer
```python
class RhythmAnalyzer:
    def detect_tempo(self, y: np.ndarray, sr: int) -> float
    def track_beats(self, y: np.ndarray, sr: int) -> tuple[float, np.ndarray]
    def detect_onsets(self, y: np.ndarray, sr: int) -> np.ndarray
```

### HarmonicAnalyzer
```python
class HarmonicAnalyzer:
    def extract_pitch(self, y: np.ndarray, sr: int) -> np.ndarray
    def extract_chroma(self, y: np.ndarray, sr: int) -> np.ndarray
    def detect_key(self, y: np.ndarray, sr: int) -> str
```

### AnalysisResult
```python
@dataclass
class AnalysisResult:
    file_path: Path
    duration: float
    sample_rate: int
    spectral: dict
    rhythm: dict
    harmonic: dict
    timbre: dict
    metadata: dict
    timestamp: float

    def to_json(self, output_path: Path) -> None
    def to_dict(self) -> dict
```

## 테스트 계획

### 단위 테스트
1. **SpectralAnalyzer 테스트**
   - STFT 계산 정확성
   - Mel-spectrogram 형태 확인
   - MFCC 차원 검증

2. **RhythmAnalyzer 테스트**
   - 템포 감지 범위 확인
   - 비트 위치 검증
   - Onset 감지 정확성

3. **MetadataExtractor 테스트**
   - ID3 태그 파싱
   - 길이 계산 정확성
   - 다양한 포맷 지원

4. **AnalysisCache 테스트**
   - 저장/로드 일관성
   - TTL 만료 처리
   - 해시 충돌 처리

### 통합 테스트
- 실제 오디오 파일로 전체 분석 파이프라인 테스트
- 성능 벤치마크 (파일 크기별)

### 성능 목표
- 3분 오디오 파일 분석: <10초
- 메모리 사용: <500MB
- 캐시 적중 시: <100ms

## 의존성 추가

requirements.txt에 추가할 패키지:
```
librosa>=0.10.0
mutagen>=1.47.0
h5py>=3.9.0
numba>=0.58.0  # librosa 성능 향상
resampy>=0.4.2  # 리샘플링
```

## Phase 1과의 통합

AudioPlayer 업데이트:
```python
# src/audio/player.py에 추가

def get_audio_data(self) -> tuple[np.ndarray, int]:
    """
    오디오 데이터 반환 (librosa 사용)

    Returns:
        (audio_data, sample_rate)
    """
    import librosa
    y, sr = librosa.load(str(self._file_path), sr=self._sample_rate)
    return y, sr

def get_duration_accurate(self) -> float:
    """
    정확한 오디오 길이 반환

    Returns:
        길이 (초)
    """
    import librosa
    return librosa.get_duration(path=str(self._file_path))
```

## 다음 단계

Phase 2 완료 후:
- Phase 3에서 분석 데이터를 시각화
- 실시간 분석 및 시각화 연동
- 특성 선택 및 필터링 기능 추가
