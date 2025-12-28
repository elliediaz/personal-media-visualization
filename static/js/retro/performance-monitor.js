/**
 * 성능 모니터
 *
 * 브라우저 환경에서 FPS 모니터링 및 자동 품질 조절
 */

const PerformanceMode = {
    LOW: 'low',
    MEDIUM: 'medium',
    HIGH: 'high',
    AUTO: 'auto'
};

const QualityPresets = {
    [PerformanceMode.LOW]: {
        resolutionScale: 0.5,
        particleCount: 500,
        fpsTarget: 30,
        effectsEnabled: false,
        antialiasing: false,
        shadows: false
    },
    [PerformanceMode.MEDIUM]: {
        resolutionScale: 0.75,
        particleCount: 2000,
        fpsTarget: 45,
        effectsEnabled: true,
        antialiasing: false,
        shadows: false
    },
    [PerformanceMode.HIGH]: {
        resolutionScale: 1.0,
        particleCount: 5000,
        fpsTarget: 60,
        effectsEnabled: true,
        antialiasing: true,
        shadows: true
    }
};

/**
 * 모바일 또는 저성능 기기 감지
 */
function detectLowEndDevice() {
    // 모바일 감지
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

    // 하드웨어 동시성 확인 (코어 수)
    const cores = navigator.hardwareConcurrency || 4;
    const isLowCores = cores <= 2;

    // 디바이스 메모리 확인 (GB)
    const memory = navigator.deviceMemory || 4;
    const isLowMemory = memory <= 2;

    // WebGL 지원 확인
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    const hasWebGL = !!gl;

    // GPU 정보 확인
    let isLowGPU = false;
    if (gl) {
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        if (debugInfo) {
            const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
            // 저성능 GPU 패턴
            const lowGPUPatterns = ['intel', 'mali', 'adreno 3', 'adreno 4', 'powervr'];
            isLowGPU = lowGPUPatterns.some(p => renderer.toLowerCase().includes(p));
        }
    }

    return {
        isMobile,
        isLowCores,
        isLowMemory,
        isLowGPU,
        hasWebGL,
        isLowEnd: isMobile || isLowCores || isLowMemory || isLowGPU
    };
}

/**
 * 성능 모니터 클래스
 */
class PerformanceMonitor {
    constructor(config = {}) {
        this.config = {
            minFps: config.minFps || 25,
            targetFps: config.targetFps || 30,
            checkInterval: config.checkInterval || 1000, // ms
            historySize: config.historySize || 60,
            ...config
        };

        // 기기 정보
        this.deviceInfo = detectLowEndDevice();

        // 상태
        this.currentMode = this.deviceInfo.isLowEnd ? PerformanceMode.MEDIUM : PerformanceMode.HIGH;
        this.frameTimes = [];
        this.lastCheckTime = performance.now();
        this.lastFrameTime = performance.now();

        // 콜백
        this.onModeChange = null;

        // 초기화
        this._init();

        console.log(`[PerformanceMonitor] 초기화 완료 (저성능 기기: ${this.deviceInfo.isLowEnd})`);
    }

    _init() {
        // 저성능 기기면 중간 품질로 시작
        if (this.deviceInfo.isLowEnd) {
            this.currentMode = PerformanceMode.MEDIUM;
            console.log('[PerformanceMonitor] 저성능 기기 감지 - 중간 품질 모드로 시작');
        }

        // WebGL 미지원시 저품질
        if (!this.deviceInfo.hasWebGL) {
            this.currentMode = PerformanceMode.LOW;
            console.log('[PerformanceMonitor] WebGL 미지원 - 저품질 모드로 시작');
        }
    }

    /**
     * 프레임 틱
     * @returns {number} 현재 FPS
     */
    tick() {
        const currentTime = performance.now();
        const delta = currentTime - this.lastFrameTime;
        this.lastFrameTime = currentTime;

        if (delta > 0) {
            this.frameTimes.push(delta);
            if (this.frameTimes.length > this.config.historySize) {
                this.frameTimes.shift();
            }
        }

        // 주기적 성능 체크
        if (currentTime - this.lastCheckTime >= this.config.checkInterval) {
            this._checkPerformance();
            this.lastCheckTime = currentTime;
        }

        return this.getFps();
    }

    /**
     * 현재 FPS 조회
     * @returns {number} 평균 FPS
     */
    getFps() {
        if (this.frameTimes.length === 0) return 0;

        const avgDelta = this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length;
        return avgDelta > 0 ? 1000 / avgDelta : 0;
    }

    /**
     * 성능 체크 및 자동 조절
     */
    _checkPerformance() {
        const fps = this.getFps();
        const newMode = this._determineMode(fps);

        if (newMode !== this.currentMode) {
            this._changeMode(newMode);
        }
    }

    /**
     * 적절한 성능 모드 결정
     * @param {number} fps - 현재 FPS
     * @returns {string} 권장 성능 모드
     */
    _determineMode(fps) {
        const currentMode = this.currentMode;

        // FPS 기반 조절
        if (fps < this.config.minFps) {
            // 성능 저하 - 품질 낮춤
            if (currentMode === PerformanceMode.HIGH) {
                return PerformanceMode.MEDIUM;
            } else if (currentMode === PerformanceMode.MEDIUM) {
                return PerformanceMode.LOW;
            }
        } else if (fps > this.config.targetFps * 1.2) {
            // 여유 있음 - 품질 높임
            if (currentMode === PerformanceMode.LOW) {
                return PerformanceMode.MEDIUM;
            } else if (currentMode === PerformanceMode.MEDIUM) {
                return PerformanceMode.HIGH;
            }
        }

        return currentMode;
    }

    /**
     * 성능 모드 변경
     * @param {string} newMode - 새 성능 모드
     */
    _changeMode(newMode) {
        const oldMode = this.currentMode;
        this.currentMode = newMode;

        console.log(`[PerformanceMonitor] 모드 변경: ${oldMode} -> ${newMode}`);

        // 콜백 호출
        if (this.onModeChange) {
            const settings = QualityPresets[newMode];
            this.onModeChange(newMode, settings);
        }
    }

    /**
     * 현재 품질 설정 조회
     * @returns {Object} 품질 설정
     */
    getQualitySettings() {
        return QualityPresets[this.currentMode];
    }

    /**
     * 성능 모드 수동 설정
     * @param {string} mode - 성능 모드
     */
    setMode(mode) {
        if (mode !== PerformanceMode.AUTO) {
            this._changeMode(mode);
        }
    }

    /**
     * 시스템 정보 조회
     * @returns {Object} 시스템 정보
     */
    getSystemInfo() {
        return {
            deviceInfo: this.deviceInfo,
            currentFps: this.getFps(),
            currentMode: this.currentMode,
            qualitySettings: this.getQualitySettings()
        };
    }
}

/**
 * 프레임 레이트 제한기 클래스
 */
class FrameRateLimiter {
    constructor(targetFps = 60) {
        this.targetFps = targetFps;
        this.frameDuration = 1000 / targetFps;
        this.lastFrameTime = performance.now();
        this.animationFrameId = null;
    }

    /**
     * 다음 프레임 실행
     * @param {Function} callback - 프레임 콜백
     */
    requestFrame(callback) {
        const currentTime = performance.now();
        const elapsed = currentTime - this.lastFrameTime;

        if (elapsed >= this.frameDuration) {
            this.lastFrameTime = currentTime - (elapsed % this.frameDuration);
            callback(elapsed);
        }

        this.animationFrameId = requestAnimationFrame(() => this.requestFrame(callback));
    }

    /**
     * 프레임 루프 시작
     * @param {Function} callback - 프레임 콜백
     */
    start(callback) {
        this.requestFrame(callback);
    }

    /**
     * 프레임 루프 중지
     */
    stop() {
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
    }

    /**
     * 목표 FPS 설정
     * @param {number} fps - 목표 FPS
     */
    setTargetFps(fps) {
        this.targetFps = fps;
        this.frameDuration = 1000 / fps;
    }
}

/**
 * FPS 디스플레이 클래스
 */
class FpsDisplay {
    constructor(container = document.body) {
        this.element = document.createElement('div');
        this.element.style.cssText = `
            position: fixed;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: #00ff00;
            font-family: monospace;
            font-size: 12px;
            padding: 5px 10px;
            border-radius: 3px;
            z-index: 10000;
            pointer-events: none;
        `;
        container.appendChild(this.element);
    }

    /**
     * FPS 업데이트
     * @param {number} fps - 현재 FPS
     * @param {string} mode - 현재 모드
     */
    update(fps, mode = '') {
        const color = fps < 30 ? '#ff0000' : fps < 45 ? '#ffff00' : '#00ff00';
        this.element.style.color = color;
        this.element.textContent = `FPS: ${fps.toFixed(1)} ${mode ? `[${mode}]` : ''}`;
    }

    /**
     * 디스플레이 제거
     */
    remove() {
        this.element.remove();
    }

    /**
     * 표시/숨김 토글
     */
    toggle() {
        this.element.style.display = this.element.style.display === 'none' ? 'block' : 'none';
    }
}

// 전역 인스턴스
let performanceMonitorInstance = null;

/**
 * 전역 성능 모니터 조회
 * @param {Object} config - 설정
 * @returns {PerformanceMonitor} 성능 모니터 인스턴스
 */
function getPerformanceMonitor(config = {}) {
    if (!performanceMonitorInstance) {
        performanceMonitorInstance = new PerformanceMonitor(config);
    }
    return performanceMonitorInstance;
}

// 모듈 내보내기
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        PerformanceMode,
        QualityPresets,
        PerformanceMonitor,
        FrameRateLimiter,
        FpsDisplay,
        detectLowEndDevice,
        getPerformanceMonitor
    };
}
