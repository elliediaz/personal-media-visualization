/**
 * CRT 렌더러
 *
 * PixiJS 기반 CRT 효과 렌더링 시스템
 */

class CRTRenderer {
    constructor(options = {}) {
        this.options = {
            container: options.container || document.body,
            width: options.width || 800,
            height: options.height || 600,
            backgroundColor: options.backgroundColor || 0x000000,
            ...options
        };

        // 효과 파라미터
        this.effects = {
            scanlines: {
                enabled: true,
                intensity: 0.3,
                count: 480
            },
            chromatic: {
                enabled: true,
                offset: 2.0
            },
            noise: {
                enabled: true,
                intensity: 0.05
            },
            vignette: {
                enabled: true,
                intensity: 0.6,
                radius: 0.8
            },
            bloom: {
                enabled: true,
                intensity: 0.3
            },
            curvature: {
                enabled: false,
                amount: 0.03
            }
        };

        this.app = null;
        this.crtFilter = null;
        this.contentContainer = null;
        this.time = 0;
        this.isRunning = false;

        this._init();
    }

    _init() {
        // PixiJS 앱 생성
        this.app = new PIXI.Application({
            width: this.options.width,
            height: this.options.height,
            backgroundColor: this.options.backgroundColor,
            resolution: window.devicePixelRatio || 1,
            autoDensity: true,
            antialias: false // CRT 효과를 위해 안티앨리어싱 비활성화
        });

        // 컨테이너에 추가
        if (typeof this.options.container === 'string') {
            document.querySelector(this.options.container).appendChild(this.app.view);
        } else {
            this.options.container.appendChild(this.app.view);
        }

        // 콘텐츠 컨테이너
        this.contentContainer = new PIXI.Container();
        this.app.stage.addChild(this.contentContainer);

        // CRT 필터 생성
        this._createCRTFilter();
    }

    _createCRTFilter() {
        // GLSL 셰이더를 사용한 커스텀 필터
        const fragmentShader = `
            precision mediump float;

            varying vec2 vTextureCoord;
            uniform sampler2D uSampler;
            uniform vec2 uResolution;
            uniform float uTime;
            uniform float uScanlineIntensity;
            uniform float uScanlineCount;
            uniform float uChromaticOffset;
            uniform float uNoiseIntensity;
            uniform float uVignetteIntensity;
            uniform float uVignetteRadius;
            uniform float uBloomIntensity;
            uniform float uCurvature;

            float random(vec2 co) {
                return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
            }

            vec2 curveCoords(vec2 uv) {
                if (uCurvature <= 0.0) return uv;
                vec2 curved = uv * 2.0 - 1.0;
                float r2 = curved.x * curved.x + curved.y * curved.y;
                curved *= 1.0 + uCurvature * r2;
                return curved * 0.5 + 0.5;
            }

            vec3 chromaticAberration(vec2 uv) {
                float offset = uChromaticOffset / uResolution.x;
                vec2 center = uv - 0.5;
                float dist = length(center);
                float radialOffset = offset * dist * 2.0;

                float r = texture2D(uSampler, uv + vec2(radialOffset, 0.0)).r;
                float g = texture2D(uSampler, uv).g;
                float b = texture2D(uSampler, uv - vec2(radialOffset, 0.0)).b;

                return vec3(r, g, b);
            }

            float scanlines(vec2 uv) {
                float scanline = sin(uv.y * uScanlineCount * 3.14159) * 0.5 + 0.5;
                return 1.0 - (1.0 - scanline) * uScanlineIntensity;
            }

            float vignette(vec2 uv) {
                vec2 center = uv - 0.5;
                float dist = length(center);
                float vig = smoothstep(uVignetteRadius, uVignetteRadius - 0.3, dist);
                return mix(1.0, vig, uVignetteIntensity);
            }

            float noise(vec2 uv) {
                return random(uv + vec2(uTime * 0.1, 0.0)) * uNoiseIntensity;
            }

            void main(void) {
                vec2 uv = curveCoords(vTextureCoord);

                if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
                    gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
                    return;
                }

                vec3 color = chromaticAberration(uv);
                color *= scanlines(uv);
                color += vec3(noise(uv) - uNoiseIntensity * 0.5);
                color *= vignette(uv);
                color = clamp(color, 0.0, 1.0);

                gl_FragColor = vec4(color, 1.0);
            }
        `;

        // 커스텀 필터 생성
        this.crtFilter = new PIXI.Filter(null, fragmentShader, {
            uResolution: [this.options.width, this.options.height],
            uTime: 0,
            uScanlineIntensity: this.effects.scanlines.intensity,
            uScanlineCount: this.effects.scanlines.count,
            uChromaticOffset: this.effects.chromatic.offset,
            uNoiseIntensity: this.effects.noise.intensity,
            uVignetteIntensity: this.effects.vignette.intensity,
            uVignetteRadius: this.effects.vignette.radius,
            uBloomIntensity: this.effects.bloom.intensity,
            uCurvature: this.effects.curvature.enabled ? this.effects.curvature.amount : 0
        });

        this.app.stage.filters = [this.crtFilter];
    }

    /**
     * 효과 파라미터 업데이트
     */
    updateEffects(newEffects) {
        Object.assign(this.effects, newEffects);

        if (this.crtFilter) {
            this.crtFilter.uniforms.uScanlineIntensity =
                this.effects.scanlines.enabled ? this.effects.scanlines.intensity : 0;
            this.crtFilter.uniforms.uScanlineCount = this.effects.scanlines.count;
            this.crtFilter.uniforms.uChromaticOffset =
                this.effects.chromatic.enabled ? this.effects.chromatic.offset : 0;
            this.crtFilter.uniforms.uNoiseIntensity =
                this.effects.noise.enabled ? this.effects.noise.intensity : 0;
            this.crtFilter.uniforms.uVignetteIntensity =
                this.effects.vignette.enabled ? this.effects.vignette.intensity : 0;
            this.crtFilter.uniforms.uVignetteRadius = this.effects.vignette.radius;
            this.crtFilter.uniforms.uBloomIntensity =
                this.effects.bloom.enabled ? this.effects.bloom.intensity : 0;
            this.crtFilter.uniforms.uCurvature =
                this.effects.curvature.enabled ? this.effects.curvature.amount : 0;
        }
    }

    /**
     * 이미지 로드 및 표시
     */
    loadImage(url) {
        return new Promise((resolve, reject) => {
            // 기존 콘텐츠 제거
            this.contentContainer.removeChildren();

            // 이미지 로드
            const sprite = PIXI.Sprite.from(url);
            sprite.texture.baseTexture.on('loaded', () => {
                // 이미지 크기 조정
                const scale = Math.min(
                    this.options.width / sprite.width,
                    this.options.height / sprite.height
                );
                sprite.scale.set(scale);
                sprite.x = (this.options.width - sprite.width) / 2;
                sprite.y = (this.options.height - sprite.height) / 2;

                this.contentContainer.addChild(sprite);
                resolve(sprite);
            });

            sprite.texture.baseTexture.on('error', (err) => {
                reject(err);
            });
        });
    }

    /**
     * 텍스트 추가
     */
    addText(text, options = {}) {
        const style = new PIXI.TextStyle({
            fontFamily: options.fontFamily || 'monospace',
            fontSize: options.fontSize || 24,
            fill: options.fill || '#00FFFF',
            dropShadow: true,
            dropShadowColor: '#00FFFF',
            dropShadowBlur: 4,
            dropShadowDistance: 0
        });

        const textObj = new PIXI.Text(text, style);
        textObj.x = options.x || 0;
        textObj.y = options.y || 0;

        this.contentContainer.addChild(textObj);
        return textObj;
    }

    /**
     * 애니메이션 시작
     */
    start() {
        if (this.isRunning) return;
        this.isRunning = true;

        this.app.ticker.add(this._update, this);
    }

    /**
     * 애니메이션 중지
     */
    stop() {
        this.isRunning = false;
        this.app.ticker.remove(this._update, this);
    }

    /**
     * 프레임 업데이트
     */
    _update(delta) {
        this.time += delta * 0.01;

        if (this.crtFilter) {
            this.crtFilter.uniforms.uTime = this.time;
        }
    }

    /**
     * CRT 효과 토글
     */
    toggleCRT(enabled) {
        this.app.stage.filters = enabled ? [this.crtFilter] : [];
    }

    /**
     * 화면 크기 조정
     */
    resize(width, height) {
        this.options.width = width;
        this.options.height = height;
        this.app.renderer.resize(width, height);

        if (this.crtFilter) {
            this.crtFilter.uniforms.uResolution = [width, height];
        }
    }

    /**
     * 스크린샷 저장
     */
    screenshot() {
        return this.app.renderer.extract.base64(this.app.stage);
    }

    /**
     * 리소스 해제
     */
    destroy() {
        this.stop();
        this.app.destroy(true, { children: true, texture: true, baseTexture: true });
    }
}

// 전역 등록
window.CRTRenderer = CRTRenderer;

// 성능 모니터
class PerformanceMonitor {
    constructor(targetFPS = 60) {
        this.targetFPS = targetFPS;
        this.frameHistory = [];
        this.historySize = 60;
        this.currentMode = 'high';
        this.callbacks = {
            high: () => {},
            medium: () => {},
            low: () => {}
        };
    }

    tick(deltaTime) {
        const fps = 1000 / (deltaTime * 16.67);
        this.frameHistory.push(fps);

        if (this.frameHistory.length > this.historySize) {
            this.frameHistory.shift();
        }

        if (this.frameHistory.length === this.historySize) {
            const avgFPS = this.frameHistory.reduce((a, b) => a + b) / this.historySize;
            this._adjustQuality(avgFPS);
        }
    }

    _adjustQuality(avgFPS) {
        const prevMode = this.currentMode;

        if (avgFPS < 25 && this.currentMode !== 'low') {
            this.currentMode = 'low';
        } else if (avgFPS < 40 && this.currentMode === 'high') {
            this.currentMode = 'medium';
        } else if (avgFPS > 55 && this.currentMode !== 'high') {
            this.currentMode = 'high';
        }

        if (prevMode !== this.currentMode) {
            this.callbacks[this.currentMode]();
        }
    }

    onModeChange(mode, callback) {
        this.callbacks[mode] = callback;
    }
}

window.PerformanceMonitor = PerformanceMonitor;
