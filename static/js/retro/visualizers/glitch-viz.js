/**
 * 글리치 시각화
 *
 * 오디오 반응형 글리치 효과
 */

class GlitchVisualizer extends BaseVisualizer {
    constructor(options = {}) {
        super(options);

        this.glitchOptions = {
            intensity: options.intensity || 0.5,
            rgbShift: options.rgbShift || true,
            scanlineNoise: options.scanlineNoise || true,
            blockGlitch: options.blockGlitch || true,
            colorInvert: options.colorInvert || false,
        };

        this.baseGraphics = null;
        this.glitchContainer = null;
        this.noiseTexture = null;

        this._initGlitch();
    }

    _initGlitch() {
        // 기본 그래픽
        this.baseGraphics = new PIXI.Graphics();
        this.container.addChild(this.baseGraphics);

        // 글리치 컨테이너
        this.glitchContainer = new PIXI.Container();
        this.container.addChild(this.glitchContainer);

        // 노이즈 텍스처 생성
        this._createNoiseTexture();
    }

    _createNoiseTexture() {
        const canvas = document.createElement('canvas');
        canvas.width = 256;
        canvas.height = 256;
        const ctx = canvas.getContext('2d');

        const imageData = ctx.createImageData(256, 256);
        for (let i = 0; i < imageData.data.length; i += 4) {
            const value = Math.random() * 255;
            imageData.data[i] = value;
            imageData.data[i + 1] = value;
            imageData.data[i + 2] = value;
            imageData.data[i + 3] = 255;
        }
        ctx.putImageData(imageData, 0, 0);

        this.noiseTexture = PIXI.Texture.from(canvas);
    }

    update(time) {
        const energy = this.getAudioFeature('energy');
        const centroid = this.getAudioFeature('centroid');
        const brightness = this.getAudioFeature('brightness');

        // 글리치 강도 조절
        this.currentIntensity = this.glitchOptions.intensity * (0.3 + energy * 0.7);

        // 기본 패턴 업데이트
        this._updateBasePattern(time, energy, centroid);
    }

    _updateBasePattern(time, energy, centroid) {
        this.baseGraphics.clear();

        const width = this.options.width;
        const height = this.options.height;

        // 배경 패턴
        const numBars = 20;
        for (let i = 0; i < numBars; i++) {
            const x = (i / numBars) * width;
            const barWidth = width / numBars;

            // 오디오 반응형 높이
            const barHeight = height * (0.3 + Math.sin(i * 0.5 + time * 3) * 0.3 * energy);

            // 색상
            const hue = (i / numBars + time * 0.1) % 1;
            const color = this.hslToRgb(hue, 0.8, 0.5);

            this.baseGraphics.beginFill(color);
            this.baseGraphics.drawRect(x, height - barHeight, barWidth - 2, barHeight);
            this.baseGraphics.endFill();
        }
    }

    render() {
        const energy = this.getAudioFeature('energy', 0.5);
        const intensity = this.currentIntensity || this.glitchOptions.intensity;

        // 글리치 효과 적용
        this.glitchContainer.removeChildren();

        if (intensity > 0.1) {
            // RGB 시프트
            if (this.glitchOptions.rgbShift && energy > 0.3) {
                this._applyRGBShift(intensity);
            }

            // 블록 글리치
            if (this.glitchOptions.blockGlitch && Math.random() < intensity * 0.3) {
                this._applyBlockGlitch(intensity);
            }

            // 스캔라인 노이즈
            if (this.glitchOptions.scanlineNoise) {
                this._applyScanlineNoise(intensity * energy);
            }

            // 라인 왜곡
            if (energy > 0.5) {
                this._applyLineDistortion(intensity, energy);
            }
        }
    }

    _applyRGBShift(intensity) {
        const shift = intensity * 10;

        // 빨강 채널 시프트
        const redOverlay = new PIXI.Graphics();
        redOverlay.beginFill(0xff0000, 0.1);
        redOverlay.drawRect(shift, 0, this.options.width, this.options.height);
        redOverlay.endFill();
        redOverlay.blendMode = PIXI.BLEND_MODES.ADD;
        this.glitchContainer.addChild(redOverlay);

        // 파랑 채널 시프트
        const blueOverlay = new PIXI.Graphics();
        blueOverlay.beginFill(0x0000ff, 0.1);
        blueOverlay.drawRect(-shift, 0, this.options.width, this.options.height);
        blueOverlay.endFill();
        blueOverlay.blendMode = PIXI.BLEND_MODES.ADD;
        this.glitchContainer.addChild(blueOverlay);
    }

    _applyBlockGlitch(intensity) {
        const numBlocks = Math.floor(intensity * 5) + 1;

        for (let i = 0; i < numBlocks; i++) {
            const blockWidth = 50 + Math.random() * 200;
            const blockHeight = 10 + Math.random() * 50;
            const x = Math.random() * (this.options.width - blockWidth);
            const y = Math.random() * (this.options.height - blockHeight);

            const block = new PIXI.Graphics();

            // 랜덤 색상 또는 반전
            if (Math.random() < 0.5) {
                block.beginFill(Math.random() * 0xffffff, 0.5);
            } else {
                block.beginFill(0x000000, 0.8);
            }

            block.drawRect(x, y, blockWidth, blockHeight);
            block.endFill();

            // 가끔 시프트 효과
            if (Math.random() < 0.3) {
                block.x = (Math.random() - 0.5) * 20;
            }

            this.glitchContainer.addChild(block);
        }
    }

    _applyScanlineNoise(intensity) {
        const numLines = Math.floor(intensity * 20);

        for (let i = 0; i < numLines; i++) {
            const y = Math.floor(Math.random() * this.options.height);
            const alpha = Math.random() * intensity * 0.5;

            const line = new PIXI.Graphics();
            line.beginFill(0xffffff, alpha);
            line.drawRect(0, y, this.options.width, 1 + Math.floor(Math.random() * 3));
            line.endFill();

            this.glitchContainer.addChild(line);
        }
    }

    _applyLineDistortion(intensity, energy) {
        const numDistortions = Math.floor(intensity * 3);

        for (let i = 0; i < numDistortions; i++) {
            const y = Math.floor(Math.random() * this.options.height);
            const height = 5 + Math.floor(Math.random() * 20);
            const shift = (Math.random() - 0.5) * 50 * intensity;

            const distortion = new PIXI.Graphics();
            distortion.beginFill(0x00ff00, 0.1 * energy);
            distortion.drawRect(shift, y, this.options.width, height);
            distortion.endFill();

            this.glitchContainer.addChild(distortion);
        }
    }

    /**
     * 글리치 강도 설정
     * @param {number} intensity
     */
    setIntensity(intensity) {
        this.glitchOptions.intensity = Math.max(0, Math.min(1, intensity));
    }

    /**
     * RGB 시프트 토글
     * @param {boolean} enabled
     */
    setRGBShift(enabled) {
        this.glitchOptions.rgbShift = enabled;
    }

    /**
     * 블록 글리치 토글
     * @param {boolean} enabled
     */
    setBlockGlitch(enabled) {
        this.glitchOptions.blockGlitch = enabled;
    }

    onResize(width, height) {
        this.options.width = width;
        this.options.height = height;
    }
}

window.GlitchVisualizer = GlitchVisualizer;
