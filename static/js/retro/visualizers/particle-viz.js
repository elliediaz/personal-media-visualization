/**
 * 파티클 시각화
 *
 * 오디오 반응형 파티클 시스템
 */

class ParticleVisualizer extends BaseVisualizer {
    constructor(options = {}) {
        super(options);

        this.particleOptions = {
            count: options.particleCount || 1000,
            mode: options.mode || 'scatter', // scatter, flow, explosion, orbit
            enableTrails: options.enableTrails || false,
            trailLength: options.trailLength || 5,
            colorMode: options.colorMode || 'spectrum', // spectrum, palette, mono
        };

        this.particles = [];
        this.trailHistory = [];
        this.particleContainer = null;
        this.trailGraphics = null;

        this._initParticles();
    }

    _initParticles() {
        // 파티클 컨테이너
        this.particleContainer = new PIXI.ParticleContainer(this.particleOptions.count, {
            scale: true,
            position: true,
            alpha: true,
            tint: true,
        });
        this.container.addChild(this.particleContainer);

        // 트레일 그래픽
        this.trailGraphics = new PIXI.Graphics();
        this.container.addChildAt(this.trailGraphics, 0);

        // 파티클 텍스처 생성
        const particleTexture = this._createParticleTexture();

        // 파티클 생성
        for (let i = 0; i < this.particleOptions.count; i++) {
            const particle = new PIXI.Sprite(particleTexture);
            particle.anchor.set(0.5);

            // 초기 위치 및 속성
            particle.x = this.options.width / 2;
            particle.y = this.options.height / 2;
            particle.alpha = 0.7;
            particle.scale.set(0.5);

            // 커스텀 속성
            particle.vx = 0;
            particle.vy = 0;
            particle.angle = Math.random() * Math.PI * 2;
            particle.speed = Math.random() * 2 + 1;
            particle.orbitRadius = Math.random() * 200 + 50;
            particle.orbitSpeed = (Math.random() - 0.5) * 0.02;

            this.particles.push(particle);
            this.particleContainer.addChild(particle);
        }
    }

    _createParticleTexture() {
        const graphics = new PIXI.Graphics();
        graphics.beginFill(0xffffff);
        graphics.drawCircle(0, 0, 8);
        graphics.endFill();
        return this.app.renderer.generateTexture(graphics);
    }

    update(time) {
        const energy = this.getAudioFeature('energy');
        const centroid = this.getAudioFeature('centroid');
        const brightness = this.getAudioFeature('brightness');

        const centerX = this.options.width / 2;
        const centerY = this.options.height / 2;

        // 트레일 히스토리 저장
        if (this.particleOptions.enableTrails) {
            const positions = this.particles.map(p => ({ x: p.x, y: p.y, tint: p.tint }));
            this.trailHistory.push(positions);
            if (this.trailHistory.length > this.particleOptions.trailLength) {
                this.trailHistory.shift();
            }
        }

        // 파티클 업데이트
        this.particles.forEach((particle, i) => {
            switch (this.particleOptions.mode) {
                case 'flow':
                    this._updateFlowParticle(particle, time, energy, centroid);
                    break;
                case 'explosion':
                    this._updateExplosionParticle(particle, time, energy, centerX, centerY);
                    break;
                case 'orbit':
                    this._updateOrbitParticle(particle, time, centroid, brightness, centerX, centerY);
                    break;
                default:
                    this._updateScatterParticle(particle, energy, centerX, centerY);
            }

            // 크기 (에너지 기반)
            const baseScale = 0.3 + energy * 0.5;
            const pulse = 1 + Math.sin(time * 10 + i * 0.1) * energy * 0.3;
            particle.scale.set(baseScale * pulse);

            // 색상
            particle.tint = this._getParticleColor(i, time, centroid);

            // 투명도
            particle.alpha = 0.5 + energy * 0.3;
        });
    }

    _updateScatterParticle(particle, energy, centerX, centerY) {
        const distance = Math.sqrt(
            Math.pow(particle.x - centerX, 2) +
            Math.pow(particle.y - centerY, 2)
        );

        // 중심으로 끌어당기는 힘
        const pullStrength = 0.01;
        particle.vx += (centerX - particle.x) * pullStrength;
        particle.vy += (centerY - particle.y) * pullStrength;

        // 랜덤 이동
        particle.vx += (Math.random() - 0.5) * energy * 2;
        particle.vy += (Math.random() - 0.5) * energy * 2;

        // 감쇠
        particle.vx *= 0.95;
        particle.vy *= 0.95;

        particle.x += particle.vx;
        particle.y += particle.vy;
    }

    _updateFlowParticle(particle, time, energy, centroid) {
        // 소용돌이 흐름
        const flowStrength = 2 + centroid * 3;

        const dx = particle.x - this.options.width / 2;
        const dy = particle.y - this.options.height / 2;

        particle.vx = -dy * 0.01 * flowStrength + Math.sin(particle.x * 0.01 + time) * energy;
        particle.vy = dx * 0.01 * flowStrength + Math.cos(particle.y * 0.01 + time) * energy;

        particle.x += particle.vx;
        particle.y += particle.vy;

        // 경계 처리
        if (particle.x < 0) particle.x = this.options.width;
        if (particle.x > this.options.width) particle.x = 0;
        if (particle.y < 0) particle.y = this.options.height;
        if (particle.y > this.options.height) particle.y = 0;
    }

    _updateExplosionParticle(particle, time, energy, centerX, centerY) {
        const phase = (time % (Math.PI * 2)) / (Math.PI * 2);
        const radius = phase * (200 + energy * 200);

        particle.x = centerX + Math.cos(particle.angle) * radius * particle.speed;
        particle.y = centerY + Math.sin(particle.angle) * radius * particle.speed;

        // 페이드 아웃
        particle.alpha = Math.max(0, 1 - phase);
    }

    _updateOrbitParticle(particle, time, centroid, brightness, centerX, centerY) {
        particle.angle += particle.orbitSpeed * (1 + brightness);

        const wobble = Math.sin(particle.angle * 3 + time) * 10;
        const radius = particle.orbitRadius + wobble;

        particle.x = centerX + Math.cos(particle.angle) * radius;
        particle.y = centerY + Math.sin(particle.angle) * radius;
    }

    _getParticleColor(index, time, centroid) {
        switch (this.particleOptions.colorMode) {
            case 'spectrum':
                const hue = (index / this.particles.length + time * 0.05) % 1;
                return this.hslToRgb(hue, 0.8, 0.5);

            case 'palette':
                // Synthwave 팔레트
                const colors = [0xff00ff, 0x00ffff, 0xff0080, 0x8000ff, 0x00ff80];
                return colors[index % colors.length];

            case 'mono':
                const brightness = 0.3 + centroid * 0.7;
                return this.hslToRgb(0.5, 0.8, brightness);

            default:
                return 0xffffff;
        }
    }

    render() {
        // 트레일 렌더링
        if (this.particleOptions.enableTrails && this.trailHistory.length > 0) {
            this.trailGraphics.clear();

            this.trailHistory.forEach((positions, historyIndex) => {
                const alpha = (historyIndex + 1) / (this.trailHistory.length + 1) * 0.3;

                positions.forEach((pos, i) => {
                    if (i % 10 === 0) { // 성능을 위해 일부만 렌더링
                        this.trailGraphics.beginFill(pos.tint || 0xffffff, alpha);
                        this.trailGraphics.drawCircle(pos.x, pos.y, 2);
                        this.trailGraphics.endFill();
                    }
                });
            });
        }
    }

    /**
     * 파티클 모드 변경
     * @param {string} mode - 모드 이름
     */
    setMode(mode) {
        this.particleOptions.mode = mode;

        // 모드 변경 시 파티클 초기화
        const centerX = this.options.width / 2;
        const centerY = this.options.height / 2;

        this.particles.forEach((particle, i) => {
            particle.x = centerX;
            particle.y = centerY;
            particle.angle = (i / this.particles.length) * Math.PI * 2;
            particle.orbitRadius = 50 + (i / this.particles.length) * 200;
        });
    }

    /**
     * 트레일 활성화/비활성화
     * @param {boolean} enabled
     */
    setTrails(enabled) {
        this.particleOptions.enableTrails = enabled;
        if (!enabled) {
            this.trailHistory = [];
            this.trailGraphics.clear();
        }
    }

    onResize(width, height) {
        this.options.width = width;
        this.options.height = height;
    }
}

window.ParticleVisualizer = ParticleVisualizer;
