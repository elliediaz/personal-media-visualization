/**
 * 매트릭스 레인 시각화
 *
 * 영화 매트릭스 스타일의 떨어지는 문자 효과
 */

class MatrixRainVisualizer extends BaseVisualizer {
    constructor(options = {}) {
        super(options);

        this.matrixOptions = {
            fontSize: options.fontSize || 14,
            columnSpacing: options.columnSpacing || 1.2,
            rainSpeed: options.rainSpeed || 1.0,
            trailLength: options.trailLength || 20,
            glitchRate: options.glitchRate || 0.02,
        };

        // 매트릭스 문자 세트
        this.chars = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789!@#$%^&*';

        this.columns = [];
        this.textContainer = null;

        this._initMatrix();
    }

    _initMatrix() {
        this.textContainer = new PIXI.Container();
        this.container.addChild(this.textContainer);

        this._initColumns();
    }

    _initColumns() {
        const columnWidth = this.matrixOptions.fontSize * this.matrixOptions.columnSpacing;
        const numColumns = Math.ceil(this.options.width / columnWidth);
        const numRows = Math.ceil(this.options.height / this.matrixOptions.fontSize) + this.matrixOptions.trailLength;

        this.columns = [];

        for (let i = 0; i < numColumns; i++) {
            const column = {
                x: i * columnWidth,
                y: Math.random() * -this.options.height,
                speed: 0.5 + Math.random() * 1.5,
                length: 5 + Math.floor(Math.random() * 15),
                chars: [],
                texts: [],
            };

            // 문자 생성
            for (let j = 0; j < numRows; j++) {
                column.chars.push(this._randomChar());

                const text = new PIXI.Text(column.chars[j], {
                    fontFamily: 'monospace',
                    fontSize: this.matrixOptions.fontSize,
                    fill: 0x00ff00,
                });
                text.x = column.x;
                text.y = j * this.matrixOptions.fontSize;
                text.alpha = 0;

                column.texts.push(text);
                this.textContainer.addChild(text);
            }

            this.columns.push(column);
        }
    }

    _randomChar() {
        return this.chars[Math.floor(Math.random() * this.chars.length)];
    }

    update(time) {
        const energy = this.getAudioFeature('energy');
        const centroid = this.getAudioFeature('centroid');
        const speedMultiplier = this.matrixOptions.rainSpeed * (0.5 + energy);

        this.columns.forEach(column => {
            // 위치 업데이트
            column.y += column.speed * speedMultiplier * 3;

            // 화면 밖으로 나가면 리셋
            if (column.y > this.options.height + column.length * this.matrixOptions.fontSize) {
                column.y = -column.length * this.matrixOptions.fontSize;
                column.speed = 0.5 + Math.random() * 1.5;
                column.length = 5 + Math.floor(Math.random() * 15);
            }

            // 글리치 효과 (랜덤 문자 변경)
            if (Math.random() < this.matrixOptions.glitchRate * (1 + energy)) {
                const idx = Math.floor(Math.random() * column.chars.length);
                column.chars[idx] = this._randomChar();
                column.texts[idx].text = column.chars[idx];
            }
        });
    }

    render() {
        const energy = this.getAudioFeature('energy', 0.5);

        this.columns.forEach(column => {
            const headY = column.y;

            column.texts.forEach((text, i) => {
                const charY = headY - i * this.matrixOptions.fontSize;

                // 가시 범위 체크
                if (charY < -this.matrixOptions.fontSize || charY > this.options.height) {
                    text.alpha = 0;
                    return;
                }

                // 트레일 내 위치
                const posInTrail = i;

                if (posInTrail === 0) {
                    // 헤드 (흰색, 밝음)
                    text.tint = 0xffffff;
                    text.alpha = 1.0;
                } else if (posInTrail < column.length) {
                    // 테일 (녹색, 점점 어두워짐)
                    const fade = 1.0 - (posInTrail / column.length);
                    text.alpha = fade * (0.7 + energy * 0.3);

                    // 녹색 강도
                    const greenIntensity = Math.floor(128 + fade * 127);
                    text.tint = (greenIntensity << 8);
                } else {
                    text.alpha = 0;
                }

                text.y = charY;
            });
        });
    }

    /**
     * 속도 설정
     * @param {number} speed
     */
    setSpeed(speed) {
        this.matrixOptions.rainSpeed = speed;
    }

    /**
     * 트레일 길이 설정
     * @param {number} length
     */
    setTrailLength(length) {
        this.matrixOptions.trailLength = length;
        this.columns.forEach(col => {
            col.length = 5 + Math.floor(Math.random() * length);
        });
    }

    onResize(width, height) {
        this.options.width = width;
        this.options.height = height;

        // 컬럼 재초기화
        this.textContainer.removeChildren();
        this._initColumns();
    }
}

window.MatrixRainVisualizer = MatrixRainVisualizer;
