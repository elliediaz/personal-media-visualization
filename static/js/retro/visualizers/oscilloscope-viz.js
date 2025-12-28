/**
 * 오실로스코프 시각화
 *
 * 클래식 오실로스코프 스타일의 파형 표시
 */

class OscilloscopeVisualizer extends BaseVisualizer {
    constructor(options = {}) {
        super(options);

        this.oscOptions = {
            style: options.style || 'neon', // neon, classic, spectrum
            showGrid: options.showGrid !== false,
            mode: options.mode || 'waveform', // waveform, lissajous, xy
            glowIntensity: options.glowIntensity || 0.8,
        };

        this.waveformData = new Float32Array(1024);
        this.waveGraphics = null;
        this.glowGraphics = null;
        this.gridGraphics = null;

        this._initGraphics();
    }

    _initGraphics() {
        // 그리드
        this.gridGraphics = new PIXI.Graphics();
        this.container.addChild(this.gridGraphics);

        // 글로우 레이어
        this.glowGraphics = new PIXI.Graphics();
        this.container.addChild(this.glowGraphics);

        // 메인 파형
        this.waveGraphics = new PIXI.Graphics();
        this.container.addChild(this.waveGraphics);

        if (this.oscOptions.showGrid) {
            this._drawGrid();
        }
    }

    _drawGrid() {
        const width = this.options.width;
        const height = this.options.height;
        const gridColor = 0x204020;
        const centerColor = 0x306030;

        this.gridGraphics.clear();
        this.gridGraphics.lineStyle(1, gridColor, 0.3);

        // 수직선
        const numVertical = 20;
        for (let i = 0; i <= numVertical; i++) {
            const x = (i / numVertical) * width;
            this.gridGraphics.moveTo(x, 0);
            this.gridGraphics.lineTo(x, height);
        }

        // 수평선
        const numHorizontal = 10;
        for (let i = 0; i <= numHorizontal; i++) {
            const y = (i / numHorizontal) * height;
            this.gridGraphics.moveTo(0, y);
            this.gridGraphics.lineTo(width, y);
        }

        // 중심선
        this.gridGraphics.lineStyle(2, centerColor, 0.5);
        this.gridGraphics.moveTo(0, height / 2);
        this.gridGraphics.lineTo(width, height / 2);
        this.gridGraphics.moveTo(width / 2, 0);
        this.gridGraphics.lineTo(width / 2, height);
    }

    /**
     * 파형 데이터 설정
     * @param {Float32Array} data - 파형 데이터
     */
    setWaveformData(data) {
        this.waveformData = data;
    }

    update(time) {
        const energy = this.getAudioFeature('energy');
        const centroid = this.getAudioFeature('centroid');
        const brightness = this.getAudioFeature('brightness');

        // 시뮬레이션 파형 생성 (실제 오디오 데이터가 없을 때)
        if (!this.realtimeData || !this.realtimeData.waveform) {
            this._generateSimulatedWaveform(time, energy, centroid, brightness);
        }
    }

    _generateSimulatedWaveform(time, energy, centroid, brightness) {
        const len = this.waveformData.length;

        for (let i = 0; i < len; i++) {
            const x = i / len;

            // 다중 주파수 합성
            const wave1 = Math.sin(x * Math.PI * 4 + time * 5) * energy;
            const wave2 = Math.sin(x * Math.PI * 6 + time * 3) * 0.5 * centroid;
            const wave3 = Math.sin(x * Math.PI * 10 - time * 2) * 0.3 * brightness;

            this.waveformData[i] = (wave1 + wave2 + wave3) * 0.8;
        }
    }

    render() {
        const width = this.options.width;
        const height = this.options.height;
        const centerY = height / 2;
        const amplitude = height * 0.4;

        this.waveGraphics.clear();
        this.glowGraphics.clear();

        if (this.oscOptions.mode === 'lissajous') {
            this._renderLissajous(width, height, amplitude);
        } else {
            this._renderWaveform(width, height, centerY, amplitude);
        }
    }

    _renderWaveform(width, height, centerY, amplitude) {
        const energy = this.getAudioFeature('energy', 0.5);
        const len = this.waveformData.length;

        // 글로우 효과 (여러 레이어)
        if (this.oscOptions.style === 'neon') {
            const glowLayers = [
                { width: 12, alpha: 0.1 },
                { width: 6, alpha: 0.2 },
                { width: 3, alpha: 0.4 },
            ];

            glowLayers.forEach(layer => {
                this.glowGraphics.lineStyle(layer.width, this._getLineColor(), layer.alpha * this.oscOptions.glowIntensity);
                this.glowGraphics.moveTo(0, centerY + this.waveformData[0] * amplitude);

                for (let i = 1; i < len; i++) {
                    const x = (i / len) * width;
                    const y = centerY + this.waveformData[i] * amplitude;
                    this.glowGraphics.lineTo(x, y);
                }
            });
        }

        // 메인 라인
        this.waveGraphics.lineStyle(2, this._getLineColor(), 0.9);
        this.waveGraphics.moveTo(0, centerY + this.waveformData[0] * amplitude);

        for (let i = 1; i < len; i++) {
            const x = (i / len) * width;
            const y = centerY + this.waveformData[i] * amplitude;
            this.waveGraphics.lineTo(x, y);
        }

        // 하이라이트 (고에너지 시)
        if (energy > 0.6 && this.oscOptions.style === 'neon') {
            this.waveGraphics.lineStyle(1, 0xffffff, (energy - 0.6) * 2);
            this.waveGraphics.moveTo(0, centerY + this.waveformData[0] * amplitude);

            for (let i = 1; i < len; i++) {
                const x = (i / len) * width;
                const y = centerY + this.waveformData[i] * amplitude;
                this.waveGraphics.lineTo(x, y);
            }
        }
    }

    _renderLissajous(width, height, amplitude) {
        const centerX = width / 2;
        const centerY = height / 2;
        const energy = this.getAudioFeature('energy', 0.5);
        const centroid = this.getAudioFeature('centroid', 0.5);

        const freqRatio = 2 + Math.floor(centroid * 5);
        const phase = this.time * 2;
        const points = 2000;

        // 글로우 레이어
        const glowLayers = [
            { width: 8, alpha: 0.1 },
            { width: 4, alpha: 0.3 },
            { width: 2, alpha: 0.5 },
        ];

        glowLayers.forEach(layer => {
            this.glowGraphics.lineStyle(layer.width, 0xff00ff, layer.alpha);

            for (let i = 0; i < points; i++) {
                const t = (i / points) * Math.PI * 2;
                const x = centerX + Math.sin(t + phase) * amplitude * (0.8 + energy * 0.2);
                const y = centerY + Math.sin(t * freqRatio) * amplitude * (0.8 + energy * 0.2);

                if (i === 0) {
                    this.glowGraphics.moveTo(x, y);
                } else {
                    this.glowGraphics.lineTo(x, y);
                }
            }
        });

        // 메인 라인
        this.waveGraphics.lineStyle(1, 0xff00ff, 1);

        for (let i = 0; i < points; i++) {
            const t = (i / points) * Math.PI * 2;
            const x = centerX + Math.sin(t + phase) * amplitude * (0.8 + energy * 0.2);
            const y = centerY + Math.sin(t * freqRatio) * amplitude * (0.8 + energy * 0.2);

            if (i === 0) {
                this.waveGraphics.moveTo(x, y);
            } else {
                this.waveGraphics.lineTo(x, y);
            }
        }
    }

    _getLineColor() {
        switch (this.oscOptions.style) {
            case 'neon':
                return 0x00ff80;
            case 'classic':
                return 0x33ff33;
            case 'spectrum':
                const hue = (this.time * 0.1) % 1;
                return this.hslToRgb(hue, 1, 0.5);
            default:
                return 0x00ff00;
        }
    }

    /**
     * 스타일 변경
     * @param {string} style
     */
    setStyle(style) {
        this.oscOptions.style = style;
    }

    /**
     * 모드 변경
     * @param {string} mode
     */
    setMode(mode) {
        this.oscOptions.mode = mode;
    }

    onResize(width, height) {
        this.options.width = width;
        this.options.height = height;

        if (this.oscOptions.showGrid) {
            this._drawGrid();
        }
    }
}

window.OscilloscopeVisualizer = OscilloscopeVisualizer;
