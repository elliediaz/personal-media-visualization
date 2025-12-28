/**
 * 프랙탈 시각화
 *
 * Mandelbrot/Julia 프랙탈 기반 오디오 반응형 시각화
 * WebGL 셰이더 기반 실시간 렌더링
 */

class FractalVisualizer extends BaseVisualizer {
    constructor(options = {}) {
        super(options);

        this.fractalOptions = {
            type: options.type || 'julia', // julia, mandelbrot
            maxIterations: options.maxIterations || 100,
            zoom: options.zoom || 1.0,
            centerX: options.centerX || 0,
            centerY: options.centerY || 0,
            colorScheme: options.colorScheme || 'rainbow',
        };

        // Julia 상수 프리셋
        this.juliaPresets = [
            { real: -0.7, imag: 0.27015, name: 'Classic' },
            { real: -0.4, imag: 0.6, name: 'Dendrite' },
            { real: 0.285, imag: 0.01, name: 'Spiral' },
            { real: -0.8, imag: 0.156, name: 'Galaxy' },
            { real: -0.70176, imag: -0.3842, name: 'Snowflake' },
            { real: 0.355, imag: 0.355, name: 'Flower' },
            { real: -0.1, imag: 0.651, name: 'Rabbit' },
            { real: -0.75, imag: 0.11, name: 'Double Spiral' },
        ];

        this.currentPreset = 0;
        this.juliaC = { ...this.juliaPresets[0] };
        this.fractalTexture = null;
        this.fractalSprite = null;

        this._initFractal();
    }

    _initFractal() {
        // 프랙탈 렌더링을 위한 캔버스
        this.fractalCanvas = document.createElement('canvas');
        this.fractalCanvas.width = this.options.width;
        this.fractalCanvas.height = this.options.height;
        this.fractalCtx = this.fractalCanvas.getContext('2d');

        // PixiJS 스프라이트로 표시
        this.fractalTexture = PIXI.Texture.from(this.fractalCanvas);
        this.fractalSprite = new PIXI.Sprite(this.fractalTexture);
        this.container.addChild(this.fractalSprite);

        // 초기 렌더링
        this._renderFractal();
    }

    update(time) {
        const energy = this.getAudioFeature('energy');
        const centroid = this.getAudioFeature('centroid');
        const brightness = this.getAudioFeature('brightness');

        // 프리셋 선택 (centroid 기반)
        const presetIndex = Math.floor(centroid * (this.juliaPresets.length - 1));
        if (presetIndex !== this.currentPreset) {
            this.currentPreset = presetIndex;
            this._transitionToPreset(presetIndex);
        }

        // 줌 레벨 (brightness 기반)
        this.fractalOptions.zoom = 1.0 + brightness * 3;

        // Julia 상수 미세 조정 (에너지 기반)
        this.juliaC.real = this.juliaPresets[this.currentPreset].real + (energy - 0.5) * 0.1;
        this.juliaC.imag = this.juliaPresets[this.currentPreset].imag + Math.sin(time) * energy * 0.05;

        // 이터레이션 수 조절
        this.fractalOptions.maxIterations = Math.floor(50 + energy * 100);

        // 프랙탈 재렌더링 (성능을 위해 간격 조절)
        if (Math.floor(time * 30) % 2 === 0) {
            this._renderFractal();
        }
    }

    _transitionToPreset(index) {
        const target = this.juliaPresets[index];
        // 부드러운 전환 (간단한 구현)
        this.juliaC.real = target.real;
        this.juliaC.imag = target.imag;
    }

    _renderFractal() {
        const width = this.fractalCanvas.width;
        const height = this.fractalCanvas.height;
        const imageData = this.fractalCtx.createImageData(width, height);
        const data = imageData.data;

        const zoom = this.fractalOptions.zoom;
        const centerX = this.fractalOptions.centerX;
        const centerY = this.fractalOptions.centerY;
        const maxIter = this.fractalOptions.maxIterations;

        const xRange = 3.0 / zoom;
        const yRange = (3.0 / zoom) * (height / width);

        const xMin = centerX - xRange / 2;
        const yMin = centerY - yRange / 2;

        // 저해상도 렌더링 (성능 최적화)
        const step = Math.max(1, Math.floor(4 - this.getAudioFeature('energy') * 3));

        for (let py = 0; py < height; py += step) {
            for (let px = 0; px < width; px += step) {
                let iteration;

                if (this.fractalOptions.type === 'julia') {
                    iteration = this._computeJulia(
                        xMin + (px / width) * xRange,
                        yMin + (py / height) * yRange,
                        this.juliaC.real,
                        this.juliaC.imag,
                        maxIter
                    );
                } else {
                    iteration = this._computeMandelbrot(
                        xMin + (px / width) * xRange,
                        yMin + (py / height) * yRange,
                        maxIter
                    );
                }

                const color = this._getColor(iteration, maxIter);

                // 블록 채우기
                for (let dy = 0; dy < step && py + dy < height; dy++) {
                    for (let dx = 0; dx < step && px + dx < width; dx++) {
                        const idx = ((py + dy) * width + (px + dx)) * 4;
                        data[idx] = color.r;
                        data[idx + 1] = color.g;
                        data[idx + 2] = color.b;
                        data[idx + 3] = 255;
                    }
                }
            }
        }

        this.fractalCtx.putImageData(imageData, 0, 0);
        this.fractalTexture.update();
    }

    _computeJulia(x0, y0, cReal, cImag, maxIter) {
        let x = x0;
        let y = y0;
        let iteration = 0;

        while (x * x + y * y <= 4 && iteration < maxIter) {
            const xNew = x * x - y * y + cReal;
            y = 2 * x * y + cImag;
            x = xNew;
            iteration++;
        }

        // 부드러운 색상을 위한 보간
        if (iteration < maxIter) {
            const logZn = Math.log(x * x + y * y) / 2;
            const nu = Math.log(logZn / Math.log(2)) / Math.log(2);
            iteration = iteration + 1 - nu;
        }

        return iteration;
    }

    _computeMandelbrot(x0, y0, maxIter) {
        let x = 0;
        let y = 0;
        let iteration = 0;

        while (x * x + y * y <= 4 && iteration < maxIter) {
            const xNew = x * x - y * y + x0;
            y = 2 * x * y + y0;
            x = xNew;
            iteration++;
        }

        if (iteration < maxIter) {
            const logZn = Math.log(x * x + y * y) / 2;
            const nu = Math.log(logZn / Math.log(2)) / Math.log(2);
            iteration = iteration + 1 - nu;
        }

        return iteration;
    }

    _getColor(iteration, maxIter) {
        if (iteration >= maxIter) {
            return { r: 0, g: 0, b: 0 };
        }

        const t = iteration / maxIter;

        switch (this.fractalOptions.colorScheme) {
            case 'rainbow':
                return this._rainbowColor(t);
            case 'fire':
                return this._fireColor(t);
            case 'ice':
                return this._iceColor(t);
            case 'synthwave':
                return this._synthwaveColor(t);
            default:
                return this._rainbowColor(t);
        }
    }

    _rainbowColor(t) {
        const hue = t;
        const saturation = 0.8;
        const lightness = 0.5;

        return this._hslToRgbObj(hue, saturation, lightness);
    }

    _fireColor(t) {
        const r = Math.min(255, t * 3 * 255);
        const g = Math.min(255, Math.max(0, (t - 0.33) * 3 * 255));
        const b = Math.min(255, Math.max(0, (t - 0.66) * 3 * 255));
        return { r, g, b };
    }

    _iceColor(t) {
        const r = Math.floor(t * 100);
        const g = Math.floor(100 + t * 155);
        const b = Math.floor(200 + t * 55);
        return { r, g, b };
    }

    _synthwaveColor(t) {
        // Synthwave 그라데이션
        const colors = [
            { r: 25, g: 0, b: 51 },
            { r: 102, g: 0, b: 153 },
            { r: 204, g: 0, b: 153 },
            { r: 255, g: 102, b: 178 },
            { r: 0, g: 255, b: 255 },
        ];

        const index = t * (colors.length - 1);
        const i1 = Math.floor(index);
        const i2 = Math.min(i1 + 1, colors.length - 1);
        const blend = index - i1;

        return {
            r: Math.floor(colors[i1].r * (1 - blend) + colors[i2].r * blend),
            g: Math.floor(colors[i1].g * (1 - blend) + colors[i2].g * blend),
            b: Math.floor(colors[i1].b * (1 - blend) + colors[i2].b * blend),
        };
    }

    _hslToRgbObj(h, s, l) {
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

        return {
            r: Math.round(r * 255),
            g: Math.round(g * 255),
            b: Math.round(b * 255),
        };
    }

    render() {
        // 텍스처는 update에서 이미 업데이트됨
    }

    /**
     * 프랙탈 타입 변경
     * @param {string} type
     */
    setType(type) {
        this.fractalOptions.type = type;
        this._renderFractal();
    }

    /**
     * 색상 스킴 변경
     * @param {string} scheme
     */
    setColorScheme(scheme) {
        this.fractalOptions.colorScheme = scheme;
        this._renderFractal();
    }

    /**
     * 줌 설정
     * @param {number} zoom
     */
    setZoom(zoom) {
        this.fractalOptions.zoom = zoom;
        this._renderFractal();
    }

    /**
     * 중심 위치 설정
     * @param {number} x
     * @param {number} y
     */
    setCenter(x, y) {
        this.fractalOptions.centerX = x;
        this.fractalOptions.centerY = y;
        this._renderFractal();
    }

    onResize(width, height) {
        this.options.width = width;
        this.options.height = height;

        this.fractalCanvas.width = width;
        this.fractalCanvas.height = height;

        this.fractalTexture.update();
        this._renderFractal();
    }
}

window.FractalVisualizer = FractalVisualizer;
