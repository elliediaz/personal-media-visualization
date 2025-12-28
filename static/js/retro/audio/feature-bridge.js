/**
 * Feature Bridge
 *
 * 오디오 분석 결과와 시각화를 연결하는 브릿지
 * WebSocket을 통한 서버 분석 결과 수신 지원
 */

class FeatureBridge {
    constructor(options = {}) {
        this.options = {
            websocketUrl: options.websocketUrl || null,
            updateInterval: options.updateInterval || 16, // ~60fps
            smoothingFactor: options.smoothingFactor || 0.3,
        };

        this.audioAnalyzer = null;
        this.visualizers = [];
        this.websocket = null;
        this.isRunning = false;
        this.updateLoop = null;

        // 서버에서 받은 분석 결과
        this.serverFeatures = null;

        // 스무딩된 특성
        this.smoothedFeatures = {
            energy: 0,
            bass: 0,
            mid: 0,
            high: 0,
            centroid: 0,
            brightness: 0,
        };
    }

    /**
     * 오디오 분석기 설정
     * @param {AudioAnalyzer} analyzer
     */
    setAudioAnalyzer(analyzer) {
        this.audioAnalyzer = analyzer;
    }

    /**
     * 시각화 추가
     * @param {BaseVisualizer} visualizer
     */
    addVisualizer(visualizer) {
        this.visualizers.push(visualizer);
    }

    /**
     * 시각화 제거
     * @param {BaseVisualizer} visualizer
     */
    removeVisualizer(visualizer) {
        const index = this.visualizers.indexOf(visualizer);
        if (index > -1) {
            this.visualizers.splice(index, 1);
        }
    }

    /**
     * WebSocket 연결
     * @param {string} url
     */
    connectWebSocket(url) {
        if (this.websocket) {
            this.websocket.close();
        }

        this.websocket = new WebSocket(url || this.options.websocketUrl);

        this.websocket.onopen = () => {
            console.log('FeatureBridge: WebSocket 연결됨');
        };

        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this._handleServerData(data);
            } catch (error) {
                console.error('FeatureBridge: 데이터 파싱 오류:', error);
            }
        };

        this.websocket.onerror = (error) => {
            console.error('FeatureBridge: WebSocket 오류:', error);
        };

        this.websocket.onclose = () => {
            console.log('FeatureBridge: WebSocket 연결 종료');
        };
    }

    _handleServerData(data) {
        if (data.type === 'features') {
            this.serverFeatures = data.features;
        } else if (data.type === 'analysis') {
            // 전체 분석 결과
            this.visualizers.forEach(viz => {
                if (viz.setAudioData) {
                    viz.setAudioData(data.analysis);
                }
            });
        }
    }

    /**
     * 브릿지 시작
     */
    start() {
        if (this.isRunning) return;
        this.isRunning = true;

        const update = () => {
            if (!this.isRunning) return;

            this._updateFeatures();
            this._broadcastToVisualizers();

            this.updateLoop = setTimeout(update, this.options.updateInterval);
        };

        update();
        console.log('FeatureBridge 시작됨');
    }

    /**
     * 브릿지 정지
     */
    stop() {
        this.isRunning = false;
        if (this.updateLoop) {
            clearTimeout(this.updateLoop);
            this.updateLoop = null;
        }
        console.log('FeatureBridge 정지됨');
    }

    _updateFeatures() {
        let currentFeatures;

        // 로컬 오디오 분석기 우선
        if (this.audioAnalyzer) {
            this.audioAnalyzer.update();
            currentFeatures = this.audioAnalyzer.getNormalizedFeatures();
        } else if (this.serverFeatures) {
            currentFeatures = this.serverFeatures;
        } else {
            // 시뮬레이션 데이터
            currentFeatures = this._generateSimulatedFeatures();
        }

        // 스무딩 적용
        const alpha = this.options.smoothingFactor;
        for (const key in this.smoothedFeatures) {
            if (currentFeatures[key] !== undefined) {
                this.smoothedFeatures[key] =
                    this.smoothedFeatures[key] * (1 - alpha) +
                    currentFeatures[key] * alpha;
            }
        }
    }

    _generateSimulatedFeatures() {
        const time = Date.now() / 1000;
        return {
            energy: 0.5 + Math.sin(time * 2) * 0.3,
            bass: 0.5 + Math.sin(time * 1.5) * 0.3,
            mid: 0.5 + Math.sin(time * 2.5) * 0.2,
            high: 0.5 + Math.sin(time * 3) * 0.2,
            centroid: 2000 + Math.sin(time) * 1000,
            brightness: 0.5 + Math.sin(time * 0.5) * 0.2,
        };
    }

    _broadcastToVisualizers() {
        this.visualizers.forEach(viz => {
            if (viz.updateRealtimeData) {
                viz.updateRealtimeData(this.smoothedFeatures);
            }
        });
    }

    /**
     * 현재 특성 가져오기
     * @returns {Object}
     */
    getFeatures() {
        return { ...this.smoothedFeatures };
    }

    /**
     * 서버에 분석 요청
     * @param {string} audioId
     */
    requestAnalysis(audioId) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'analyze',
                audioId: audioId,
            }));
        }
    }

    /**
     * 리소스 정리
     */
    destroy() {
        this.stop();

        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }

        this.visualizers = [];
    }
}

/**
 * 시각화 매니저
 *
 * 여러 시각화를 관리하고 전환
 */
class VisualizerManager {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ?
            document.querySelector(container) : container;

        this.options = {
            width: options.width || this.container.clientWidth || 800,
            height: options.height || this.container.clientHeight || 600,
            ...options
        };

        this.visualizers = {};
        this.activeVisualizer = null;
        this.featureBridge = new FeatureBridge();
        this.audioAnalyzer = null;
    }

    /**
     * 오디오 분석기 초기화
     */
    async initAudio() {
        this.audioAnalyzer = new AudioAnalyzer();
        await this.audioAnalyzer.init();
        this.featureBridge.setAudioAnalyzer(this.audioAnalyzer);
    }

    /**
     * 시각화 등록
     * @param {string} name
     * @param {class} VisualizerClass
     * @param {Object} options
     */
    register(name, VisualizerClass, options = {}) {
        this.visualizers[name] = {
            class: VisualizerClass,
            options: {
                container: this.container,
                width: this.options.width,
                height: this.options.height,
                ...options
            },
            instance: null,
        };
    }

    /**
     * 시각화 전환
     * @param {string} name
     */
    switchTo(name) {
        if (!this.visualizers[name]) {
            console.error(`시각화 "${name}"을 찾을 수 없음`);
            return;
        }

        // 현재 시각화 정지
        if (this.activeVisualizer) {
            this.activeVisualizer.stop();
            this.activeVisualizer.destroy();
            this.featureBridge.removeVisualizer(this.activeVisualizer);
        }

        // 새 시각화 생성
        const vizConfig = this.visualizers[name];
        vizConfig.instance = new vizConfig.class(vizConfig.options);
        this.activeVisualizer = vizConfig.instance;

        // 브릿지에 등록
        this.featureBridge.addVisualizer(this.activeVisualizer);

        // 시작
        this.activeVisualizer.start();

        console.log(`시각화 전환: ${name}`);
    }

    /**
     * 브릿지 시작
     */
    start() {
        this.featureBridge.start();
    }

    /**
     * 브릿지 정지
     */
    stop() {
        this.featureBridge.stop();
        if (this.activeVisualizer) {
            this.activeVisualizer.stop();
        }
    }

    /**
     * 오디오 엘리먼트 연결
     * @param {HTMLAudioElement} audioElement
     */
    connectAudio(audioElement) {
        if (this.audioAnalyzer) {
            this.audioAnalyzer.connectAudioElement(audioElement);
        }
    }

    /**
     * 마이크 연결
     */
    async connectMicrophone() {
        if (this.audioAnalyzer) {
            await this.audioAnalyzer.connectMicrophone();
        }
    }

    /**
     * 리소스 정리
     */
    destroy() {
        this.stop();
        this.featureBridge.destroy();

        if (this.audioAnalyzer) {
            this.audioAnalyzer.destroy();
        }

        if (this.activeVisualizer) {
            this.activeVisualizer.destroy();
        }
    }
}

window.FeatureBridge = FeatureBridge;
window.VisualizerManager = VisualizerManager;
