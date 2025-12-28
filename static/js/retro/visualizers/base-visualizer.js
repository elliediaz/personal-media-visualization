/**
 * 시각화 기본 클래스
 *
 * PixiJS 기반 시각화의 공통 기능 제공
 */

class BaseVisualizer {
    constructor(options = {}) {
        this.options = {
            container: options.container || document.body,
            width: options.width || 800,
            height: options.height || 600,
            backgroundColor: options.backgroundColor || 0x000000,
            antialias: options.antialias !== false,
            ...options
        };

        this.app = null;
        this.container = null;
        this.audioData = null;
        this.time = 0;
        this.isPlaying = false;
        this.animationId = null;

        this._init();
    }

    _init() {
        // PixiJS Application 생성
        this.app = new PIXI.Application({
            width: this.options.width,
            height: this.options.height,
            backgroundColor: this.options.backgroundColor,
            antialias: this.options.antialias,
            resolution: window.devicePixelRatio || 1,
            autoDensity: true,
        });

        // 컨테이너에 캔버스 추가
        if (typeof this.options.container === 'string') {
            document.querySelector(this.options.container).appendChild(this.app.view);
        } else {
            this.options.container.appendChild(this.app.view);
        }

        // 메인 컨테이너
        this.container = new PIXI.Container();
        this.app.stage.addChild(this.container);

        // 리사이즈 핸들러
        this._setupResize();
    }

    _setupResize() {
        window.addEventListener('resize', () => {
            const parent = this.app.view.parentElement;
            if (parent) {
                const width = parent.clientWidth;
                const height = parent.clientHeight;
                this.app.renderer.resize(width, height);
                this.onResize(width, height);
            }
        });
    }

    /**
     * 오디오 데이터 설정
     * @param {Object} data - 오디오 분석 데이터
     */
    setAudioData(data) {
        this.audioData = data;
    }

    /**
     * 실시간 오디오 데이터 업데이트
     * @param {Object} data - 실시간 오디오 특성
     */
    updateRealtimeData(data) {
        this.realtimeData = data;
    }

    /**
     * 애니메이션 시작
     */
    start() {
        if (this.isPlaying) return;
        this.isPlaying = true;
        this._animate();
    }

    /**
     * 애니메이션 정지
     */
    stop() {
        this.isPlaying = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }

    _animate() {
        if (!this.isPlaying) return;

        this.time += 0.016; // ~60fps
        this.update(this.time);
        this.render();

        this.animationId = requestAnimationFrame(() => this._animate());
    }

    /**
     * 상태 업데이트 (오버라이드 필요)
     * @param {number} time - 경과 시간
     */
    update(time) {
        // 서브클래스에서 구현
    }

    /**
     * 렌더링 (오버라이드 필요)
     */
    render() {
        // 서브클래스에서 구현
    }

    /**
     * 리사이즈 핸들러 (오버라이드 가능)
     * @param {number} width
     * @param {number} height
     */
    onResize(width, height) {
        // 서브클래스에서 오버라이드
    }

    /**
     * 정규화된 오디오 특성 가져오기
     * @param {string} feature - 특성 이름
     * @param {number} defaultValue - 기본값
     * @returns {number} 0-1 범위 값
     */
    getAudioFeature(feature, defaultValue = 0.5) {
        if (!this.realtimeData) return defaultValue;

        switch (feature) {
            case 'energy':
                return this.realtimeData.energy || defaultValue;
            case 'centroid':
                return Math.min(1, (this.realtimeData.centroid || 2000) / 8000);
            case 'brightness':
                return this.realtimeData.brightness || defaultValue;
            case 'bass':
                return this.realtimeData.bass || defaultValue;
            case 'mid':
                return this.realtimeData.mid || defaultValue;
            case 'high':
                return this.realtimeData.high || defaultValue;
            default:
                return defaultValue;
        }
    }

    /**
     * HSL to RGB 변환
     * @param {number} h - Hue (0-1)
     * @param {number} s - Saturation (0-1)
     * @param {number} l - Lightness (0-1)
     * @returns {number} RGB hex color
     */
    hslToRgb(h, s, l) {
        let r, g, b;

        if (s === 0) {
            r = g = b = l;
        } else {
            const hue2rgb = (p, q, t) => {
                if (t < 0) t += 1;
                if (t > 1) t -= 1;
                if (t < 1/6) return p + (q - p) * 6 * t;
                if (t < 1/2) return q;
                if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
                return p;
            };

            const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            const p = 2 * l - q;
            r = hue2rgb(p, q, h + 1/3);
            g = hue2rgb(p, q, h);
            b = hue2rgb(p, q, h - 1/3);
        }

        return (Math.round(r * 255) << 16) + (Math.round(g * 255) << 8) + Math.round(b * 255);
    }

    /**
     * 리소스 정리
     */
    destroy() {
        this.stop();
        if (this.app) {
            this.app.destroy(true, { children: true, texture: true, baseTexture: true });
        }
    }
}

window.BaseVisualizer = BaseVisualizer;
