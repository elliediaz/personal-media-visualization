/**
 * Personal Media Visualization - 메인 애플리케이션
 *
 * 오디오 분석 및 시각화 웹 인터페이스
 */

const API_BASE_URL = window.location.origin;

// 상태 관리
const state = {
    currentAudioId: null,
    currentAnalysisId: null,
    isProcessing: false,
    audioFile: null
};

// DOM 요소
const elements = {
    uploadArea: null,
    fileInput: null,
    audioInfo: null,
    analysisSection: null,
    visualizationSection: null,
    progressContainer: null,
    progressBar: null,
    statusText: null,
    vizPreview: null,
    vizOptions: null
};

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    initElements();
    initEventListeners();
    checkServerStatus();
});

function initElements() {
    elements.uploadArea = document.getElementById('upload-area');
    elements.fileInput = document.getElementById('file-input');
    elements.audioInfo = document.getElementById('audio-info');
    elements.analysisSection = document.getElementById('analysis-section');
    elements.visualizationSection = document.getElementById('visualization-section');
    elements.progressContainer = document.getElementById('progress-container');
    elements.progressBar = document.getElementById('progress-bar');
    elements.statusText = document.getElementById('status-text');
    elements.vizPreview = document.getElementById('viz-preview');
    elements.vizOptions = document.querySelectorAll('.viz-option');
}

function initEventListeners() {
    // 파일 업로드 영역
    if (elements.uploadArea) {
        elements.uploadArea.addEventListener('click', () => {
            elements.fileInput?.click();
        });

        elements.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            elements.uploadArea.classList.add('dragover');
        });

        elements.uploadArea.addEventListener('dragleave', () => {
            elements.uploadArea.classList.remove('dragover');
        });

        elements.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            elements.uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect(files[0]);
            }
        });
    }

    // 파일 입력
    if (elements.fileInput) {
        elements.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });
    }

    // 시각화 옵션
    elements.vizOptions.forEach(option => {
        option.addEventListener('click', () => {
            elements.vizOptions.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');
            if (state.currentAnalysisId) {
                generateVisualization(option.dataset.type);
            }
        });
    });
}

// 서버 상태 확인
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            console.log('서버 연결 정상');
        }
    } catch (error) {
        showNotification('서버에 연결할 수 없습니다.', 'error');
    }
}

// 파일 선택 처리
async function handleFileSelect(file) {
    if (!file) return;

    // 오디오 파일 확인
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/flac', 'audio/ogg', 'audio/mp4'];
    const validExtensions = ['.mp3', '.wav', '.flac', '.ogg', '.m4a'];
    const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));

    if (!validTypes.includes(file.type) && !validExtensions.includes(extension)) {
        showNotification('지원하지 않는 파일 형식입니다.', 'error');
        return;
    }

    state.audioFile = file;
    updateUploadAreaWithFile(file);
    await uploadFile(file);
}

// 업로드 영역 업데이트
function updateUploadAreaWithFile(file) {
    if (elements.uploadArea) {
        elements.uploadArea.innerHTML = `
            <div class="upload-icon">&#127925;</div>
            <div class="upload-text">
                <strong>${file.name}</strong><br>
                ${formatFileSize(file.size)}
            </div>
        `;
    }
}

// 파일 업로드
async function uploadFile(file) {
    setProcessing(true);
    updateStatus('업로드 중...', 10);

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/api/v1/audio/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('업로드 실패');
        }

        const result = await response.json();
        state.currentAudioId = result.audio_id;

        updateStatus('업로드 완료', 20);
        showAudioInfo(result.info);
        await startAnalysis();

    } catch (error) {
        showNotification(`업로드 오류: ${error.message}`, 'error');
        setProcessing(false);
    }
}

// 오디오 정보 표시
function showAudioInfo(info) {
    if (elements.audioInfo && info) {
        elements.audioInfo.innerHTML = `
            <div class="result-item">
                <div class="result-value">${formatDuration(info.duration)}</div>
                <div class="result-label">재생 시간</div>
            </div>
            <div class="result-item">
                <div class="result-value">${info.sample_rate} Hz</div>
                <div class="result-label">샘플링 레이트</div>
            </div>
            <div class="result-item">
                <div class="result-value">${info.channels}ch</div>
                <div class="result-label">채널</div>
            </div>
            <div class="result-item">
                <div class="result-value">${info.format.toUpperCase()}</div>
                <div class="result-label">포맷</div>
            </div>
        `;
        elements.audioInfo.style.display = 'grid';
    }
}

// 분석 시작
async function startAnalysis() {
    updateStatus('분석 중...', 40);

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/analysis/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                audio_id: state.currentAudioId,
                features: null,
                use_cache: true
            })
        });

        if (!response.ok) {
            throw new Error('분석 요청 실패');
        }

        const result = await response.json();
        state.currentAnalysisId = result.analysis_id;

        // 분석 완료 대기
        await waitForAnalysis(result.analysis_id);

    } catch (error) {
        showNotification(`분석 오류: ${error.message}`, 'error');
        setProcessing(false);
    }
}

// 분석 완료 대기
async function waitForAnalysis(analysisId) {
    const maxAttempts = 60;
    let attempts = 0;

    while (attempts < maxAttempts) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/analysis/${analysisId}`);
            const result = await response.json();

            if (result.status === 'completed') {
                updateStatus('분석 완료', 70);
                showAnalysisResults(result);
                enableVisualization();
                await generateVisualization('spectrogram');
                return;
            } else if (result.status === 'failed') {
                throw new Error(result.error || '분석 실패');
            }

            // 진행률 업데이트
            const progress = 40 + (attempts / maxAttempts) * 30;
            updateStatus(`분석 중... (${Math.round(progress)}%)`, progress);

        } catch (error) {
            if (error.message.includes('분석 실패')) {
                throw error;
            }
        }

        await sleep(1000);
        attempts++;
    }

    throw new Error('분석 시간 초과');
}

// 분석 결과 표시
function showAnalysisResults(result) {
    if (elements.analysisSection && result.features) {
        const features = result.features;
        let html = '<div class="analysis-results">';

        if (features.rhythm?.tempo) {
            html += `
                <div class="result-item">
                    <div class="result-value">${features.rhythm.tempo.toFixed(1)}</div>
                    <div class="result-label">BPM</div>
                </div>
            `;
        }

        if (features.harmonic?.key) {
            html += `
                <div class="result-item">
                    <div class="result-value">${features.harmonic.key}</div>
                    <div class="result-label">키</div>
                </div>
            `;
        }

        if (features.spectral?.spectral_centroid_mean) {
            html += `
                <div class="result-item">
                    <div class="result-value">${features.spectral.spectral_centroid_mean.toFixed(0)} Hz</div>
                    <div class="result-label">스펙트럼 중심</div>
                </div>
            `;
        }

        html += '</div>';
        elements.analysisSection.innerHTML = html;
        elements.analysisSection.style.display = 'block';
    }
}

// 시각화 활성화
function enableVisualization() {
    if (elements.visualizationSection) {
        elements.visualizationSection.style.display = 'block';
    }
}

// 시각화 생성
async function generateVisualization(vizType) {
    updateStatus(`${vizType} 시각화 생성 중...`, 80);

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/visualize/render`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                analysis_id: state.currentAnalysisId,
                viz_type: vizType,
                output_format: 'png',
                width: 1920,
                height: 1080,
                params: {}
            })
        });

        if (!response.ok) {
            throw new Error('시각화 생성 실패');
        }

        const result = await response.json();

        // 이미지 표시
        if (elements.vizPreview && result.file_url) {
            elements.vizPreview.innerHTML = `<img src="${result.file_url}" alt="${vizType} visualization">`;
        }

        updateStatus('완료', 100);
        setProcessing(false);
        showNotification('처리가 완료되었습니다.', 'success');

    } catch (error) {
        showNotification(`시각화 오류: ${error.message}`, 'error');
        setProcessing(false);
    }
}

// 상태 업데이트
function updateStatus(text, progress) {
    if (elements.statusText) {
        elements.statusText.textContent = text;
    }
    if (elements.progressBar) {
        elements.progressBar.style.width = `${progress}%`;
    }
    if (elements.progressContainer) {
        elements.progressContainer.style.display = progress > 0 ? 'block' : 'none';
    }
}

// 처리 중 상태 설정
function setProcessing(isProcessing) {
    state.isProcessing = isProcessing;
    document.body.style.cursor = isProcessing ? 'wait' : 'default';
}

// 알림 표시
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 4000);
}

// 유틸리티 함수
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 다운로드 기능
function downloadVisualization() {
    const img = elements.vizPreview?.querySelector('img');
    if (img) {
        const link = document.createElement('a');
        link.href = img.src;
        link.download = `visualization_${Date.now()}.png`;
        link.click();
    }
}

// CRT 효과 상태
let crtEnabled = true;

// CRT 효과 토글
function toggleCRTEffect() {
    crtEnabled = !crtEnabled;

    const toggleBtn = document.getElementById('crt-toggle');
    const vizPreview = document.getElementById('viz-preview');

    if (toggleBtn) {
        toggleBtn.classList.toggle('active', crtEnabled);
    }

    if (vizPreview) {
        vizPreview.classList.toggle('crt-enabled', crtEnabled);
    }
}

// 전역 함수 등록
window.downloadVisualization = downloadVisualization;
window.toggleCRTEffect = toggleCRTEffect;
