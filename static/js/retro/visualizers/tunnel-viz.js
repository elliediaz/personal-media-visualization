/**
 * 터널 시각화
 *
 * 사이키델릭 터널/와프 효과
 */

class TunnelVisualizer extends BaseVisualizer {
    constructor(options = {}) {
        super(options);

        this.tunnelOptions = {
            type: options.type || 'spiral', // spiral, warp, vortex, grid
            ringCount: options.ringCount || 20,
            segmentCount: options.segmentCount || 24,
            palette: options.palette || 'synthwave',
        };

        this.rings = [];
        this.tunnelGraphics = null;

        this._initTunnel();
    }

    _initTunnel() {
        this.tunnelGraphics = new PIXI.Graphics();
        this.container.addChild(this.tunnelGraphics);

        // 링 초기화
        for (let i = 0; i < this.tunnelOptions.ringCount; i++) {
            this.rings.push({
                depth: i / this.tunnelOptions.ringCount,
                rotation: 0,
                segments: [],
            });
        }
    }

    update(time) {
        const energy = this.getAudioFeature('energy');
        const centroid = this.getAudioFeature('centroid');
        const brightness = this.getAudioFeature('brightness');

        // 링 업데이트
        this.rings.forEach((ring, i) => {
            // 깊이 이동 (터널 효과)
            ring.depth += 0.01 * (1 + energy);
            if (ring.depth > 1) {
                ring.depth = 0;
            }

            // 회전
            const rotationSpeed = 0.02 * (1 - ring.depth) * (1 + centroid);
            ring.rotation += rotationSpeed;

            // 왜곡
            ring.wobble = Math.sin(time * 3 + i * 0.5) * energy * 0.2;
        });
    }

    render() {
        const width = this.options.width;
        const height = this.options.height;
        const centerX = width / 2;
        const centerY = height / 2;
        const maxRadius = Math.min(width, height) * 0.45;

        const energy = this.getAudioFeature('energy', 0.5);
        const centroid = this.getAudioFeature('centroid', 0.5);

        this.tunnelGraphics.clear();

        switch (this.tunnelOptions.type) {
            case 'warp':
                this._renderWarpTunnel(centerX, centerY, maxRadius, energy);
                break;
            case 'vortex':
                this._renderVortexTunnel(centerX, centerY, maxRadius, energy, centroid);
                break;
            case 'grid':
                this._renderGridTunnel(centerX, centerY, maxRadius, energy);
                break;
            default:
                this._renderSpiralTunnel(centerX, centerY, maxRadius, energy, centroid);
        }

        // 중심 글로우
        this._renderCenterGlow(centerX, centerY, energy);
    }

    _renderSpiralTunnel(centerX, centerY, maxRadius, energy, centroid) {
        const segmentCount = this.tunnelOptions.segmentCount;

        // 깊이순으로 정렬 (먼 것부터 그리기)
        const sortedRings = [...this.rings].sort((a, b) => b.depth - a.depth);

        sortedRings.forEach(ring => {
            const radius = ring.depth * maxRadius;
            const nextRadius = (ring.depth + 0.05) * maxRadius;

            // 밝기 (가까울수록 밝음)
            const brightness = 0.2 + ring.depth * 0.8;
            const alpha = brightness * (0.5 + energy * 0.3);

            // 세그먼트 그리기
            for (let s = 0; s < segmentCount; s++) {
                const angle1 = (s / segmentCount) * Math.PI * 2 + ring.rotation;
                const angle2 = ((s + 1) / segmentCount) * Math.PI * 2 + ring.rotation;

                // 나선 왜곡
                const spiralOffset = ring.depth * 3 * (1 + centroid);
                const adjustedAngle1 = angle1 + spiralOffset;
                const adjustedAngle2 = angle2 + spiralOffset;

                // 흔들림 적용
                const wobbleRadius = radius * (1 + ring.wobble);

                // 색상 (세그먼트별로 변화)
                const hue = ((s / segmentCount) + ring.depth + this.time * 0.1) % 1;
                const color = this._getPaletteColor(hue);

                // 세그먼트 그리기
                this.tunnelGraphics.beginFill(color, alpha);
                this.tunnelGraphics.moveTo(
                    centerX + Math.cos(adjustedAngle1) * wobbleRadius,
                    centerY + Math.sin(adjustedAngle1) * wobbleRadius
                );
                this.tunnelGraphics.lineTo(
                    centerX + Math.cos(adjustedAngle2) * wobbleRadius,
                    centerY + Math.sin(adjustedAngle2) * wobbleRadius
                );
                this.tunnelGraphics.lineTo(
                    centerX + Math.cos(adjustedAngle2 + spiralOffset * 0.05) * nextRadius,
                    centerY + Math.sin(adjustedAngle2 + spiralOffset * 0.05) * nextRadius
                );
                this.tunnelGraphics.lineTo(
                    centerX + Math.cos(adjustedAngle1 + spiralOffset * 0.05) * nextRadius,
                    centerY + Math.sin(adjustedAngle1 + spiralOffset * 0.05) * nextRadius
                );
                this.tunnelGraphics.endFill();
            }
        });
    }

    _renderWarpTunnel(centerX, centerY, maxRadius, energy) {
        const numStreaks = 32;

        for (let i = 0; i < numStreaks; i++) {
            const angle = (i / numStreaks) * Math.PI * 2;
            const length = maxRadius * (0.3 + energy * 0.7);

            // 스트릭 애니메이션
            const offset = (this.time * 2 + i * 0.1) % 1;
            const startRadius = offset * maxRadius * 0.5;
            const endRadius = startRadius + length * (0.5 + Math.random() * 0.5);

            // 글로우 레이어
            for (let layer = 0; layer < 3; layer++) {
                const layerWidth = (3 - layer) * 2;
                const layerAlpha = 0.3 - layer * 0.1;

                this.tunnelGraphics.lineStyle(layerWidth, 0xffffff, layerAlpha * energy);
                this.tunnelGraphics.moveTo(
                    centerX + Math.cos(angle) * startRadius,
                    centerY + Math.sin(angle) * startRadius
                );
                this.tunnelGraphics.lineTo(
                    centerX + Math.cos(angle) * endRadius,
                    centerY + Math.sin(angle) * endRadius
                );
            }

            // 메인 라인
            const hue = (i / numStreaks + this.time * 0.1) % 1;
            this.tunnelGraphics.lineStyle(1, this.hslToRgb(hue, 1, 0.7), 0.8);
            this.tunnelGraphics.moveTo(
                centerX + Math.cos(angle) * startRadius,
                centerY + Math.sin(angle) * startRadius
            );
            this.tunnelGraphics.lineTo(
                centerX + Math.cos(angle) * endRadius,
                centerY + Math.sin(angle) * endRadius
            );
        }
    }

    _renderVortexTunnel(centerX, centerY, maxRadius, energy, centroid) {
        const armCount = 6;
        const pointsPerArm = 100;
        const vortexStrength = 5 + centroid * 10;

        for (let arm = 0; arm < armCount; arm++) {
            const baseAngle = (arm / armCount) * Math.PI * 2 + this.time;
            const hue = (arm / armCount + this.time * 0.1) % 1;
            const color = this._getPaletteColor(hue);

            // 글로우
            this.tunnelGraphics.lineStyle(6, color, 0.2 * energy);
            this._drawVortexArm(centerX, centerY, baseAngle, maxRadius, vortexStrength, pointsPerArm);

            this.tunnelGraphics.lineStyle(3, color, 0.4 * energy);
            this._drawVortexArm(centerX, centerY, baseAngle, maxRadius, vortexStrength, pointsPerArm);

            // 메인
            this.tunnelGraphics.lineStyle(1.5, color, 0.8);
            this._drawVortexArm(centerX, centerY, baseAngle, maxRadius, vortexStrength, pointsPerArm);
        }
    }

    _drawVortexArm(centerX, centerY, baseAngle, maxRadius, vortexStrength, points) {
        for (let i = 0; i < points; i++) {
            const t = i / points;
            const radius = t * maxRadius;
            const angle = baseAngle + t * vortexStrength;

            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;

            if (i === 0) {
                this.tunnelGraphics.moveTo(x, y);
            } else {
                this.tunnelGraphics.lineTo(x, y);
            }
        }
    }

    _renderGridTunnel(centerX, centerY, maxRadius, energy) {
        const gridSize = 10;
        const perspective = 0.8;

        // 동심원 그리드
        for (let i = 1; i <= gridSize; i++) {
            const depth = i / gridSize;
            const radius = depth * maxRadius;
            const alpha = depth * (0.3 + energy * 0.4);

            // 애니메이션된 반경
            const animatedRadius = radius + Math.sin(this.time * 2 - depth * 5) * 10 * energy;

            this.tunnelGraphics.lineStyle(1, 0x00ffff, alpha);
            this.tunnelGraphics.drawCircle(centerX, centerY, animatedRadius);
        }

        // 방사형 라인
        const rayCount = 16;
        for (let i = 0; i < rayCount; i++) {
            const angle = (i / rayCount) * Math.PI * 2 + this.time * 0.5;
            const alpha = 0.3 + energy * 0.4;

            this.tunnelGraphics.lineStyle(1, 0x00ffff, alpha);
            this.tunnelGraphics.moveTo(centerX, centerY);
            this.tunnelGraphics.lineTo(
                centerX + Math.cos(angle) * maxRadius,
                centerY + Math.sin(angle) * maxRadius
            );
        }
    }

    _renderCenterGlow(centerX, centerY, energy) {
        const glowSize = 30 + energy * 20;

        // 외부 글로우
        this.tunnelGraphics.beginFill(0xffffff, 0.1 + energy * 0.2);
        this.tunnelGraphics.drawCircle(centerX, centerY, glowSize);
        this.tunnelGraphics.endFill();

        // 내부 코어
        this.tunnelGraphics.beginFill(0xffffff, 0.5 + energy * 0.3);
        this.tunnelGraphics.drawCircle(centerX, centerY, glowSize * 0.3);
        this.tunnelGraphics.endFill();
    }

    _getPaletteColor(t) {
        const palettes = {
            synthwave: [
                [0.1, 0.0, 0.2],
                [0.4, 0.0, 0.6],
                [0.8, 0.0, 0.6],
                [1.0, 0.4, 0.7],
                [0.0, 1.0, 1.0],
            ],
            neon: [
                [0.0, 1.0, 0.0],
                [0.0, 1.0, 1.0],
                [1.0, 0.0, 1.0],
                [1.0, 1.0, 0.0],
            ],
            fire: [
                [0.5, 0.0, 0.0],
                [1.0, 0.2, 0.0],
                [1.0, 0.6, 0.0],
                [1.0, 1.0, 0.2],
            ],
        };

        const palette = palettes[this.tunnelOptions.palette] || palettes.synthwave;
        const index = t * (palette.length - 1);
        const i1 = Math.floor(index);
        const i2 = Math.min(i1 + 1, palette.length - 1);
        const blend = index - i1;

        const r = palette[i1][0] * (1 - blend) + palette[i2][0] * blend;
        const g = palette[i1][1] * (1 - blend) + palette[i2][1] * blend;
        const b = palette[i1][2] * (1 - blend) + palette[i2][2] * blend;

        return (Math.floor(r * 255) << 16) + (Math.floor(g * 255) << 8) + Math.floor(b * 255);
    }

    /**
     * 터널 타입 변경
     * @param {string} type
     */
    setType(type) {
        this.tunnelOptions.type = type;
    }

    /**
     * 팔레트 변경
     * @param {string} palette
     */
    setPalette(palette) {
        this.tunnelOptions.palette = palette;
    }

    onResize(width, height) {
        this.options.width = width;
        this.options.height = height;
    }
}

window.TunnelVisualizer = TunnelVisualizer;
