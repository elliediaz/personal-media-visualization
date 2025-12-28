/**
 * Windows 95 스타일 슬라이더 컴포넌트
 */

class RetroSlider {
    constructor(options = {}) {
        this.options = {
            min: options.min || 0,
            max: options.max || 100,
            value: options.value || 50,
            step: options.step || 1,
            width: options.width || 200,
            showValue: options.showValue !== false,
            onChange: options.onChange || null,
        };

        this.element = null;
        this.track = null;
        this.thumb = null;
        this.valueDisplay = null;
        this.isDragging = false;

        this._create();
        this._bindEvents();
    }

    _create() {
        this.element = document.createElement('div');
        this.element.className = 'win95-slider';
        this.element.style.width = `${this.options.width}px`;

        // 트랙
        this.track = document.createElement('div');
        this.track.className = 'win95-slider-track';
        this.track.style.position = 'relative';

        // 썸
        this.thumb = document.createElement('div');
        this.thumb.className = 'win95-slider-thumb';
        this.thumb.style.position = 'absolute';

        this.track.appendChild(this.thumb);
        this.element.appendChild(this.track);

        // 값 표시
        if (this.options.showValue) {
            this.valueDisplay = document.createElement('span');
            this.valueDisplay.style.marginLeft = '8px';
            this.valueDisplay.style.fontFamily = 'MS Sans Serif, Tahoma, sans-serif';
            this.valueDisplay.style.fontSize = '11px';
            this.valueDisplay.style.minWidth = '30px';
            this.valueDisplay.style.textAlign = 'right';
            this.element.appendChild(this.valueDisplay);
        }

        this._updateThumbPosition();
    }

    _bindEvents() {
        this.thumb.addEventListener('mousedown', (e) => {
            e.preventDefault();
            this.isDragging = true;
            document.body.style.cursor = 'ew-resize';
        });

        this.track.addEventListener('click', (e) => {
            if (e.target === this.thumb) return;
            const rect = this.track.getBoundingClientRect();
            const ratio = (e.clientX - rect.left) / rect.width;
            this._setValueFromRatio(ratio);
        });

        document.addEventListener('mousemove', (e) => {
            if (!this.isDragging) return;
            const rect = this.track.getBoundingClientRect();
            const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
            this._setValueFromRatio(ratio);
        });

        document.addEventListener('mouseup', () => {
            this.isDragging = false;
            document.body.style.cursor = '';
        });
    }

    _setValueFromRatio(ratio) {
        const range = this.options.max - this.options.min;
        let value = this.options.min + ratio * range;
        value = Math.round(value / this.options.step) * this.options.step;
        value = Math.max(this.options.min, Math.min(this.options.max, value));

        if (value !== this.options.value) {
            this.options.value = value;
            this._updateThumbPosition();
            if (this.options.onChange) {
                this.options.onChange(value);
            }
        }
    }

    _updateThumbPosition() {
        const ratio = (this.options.value - this.options.min) / (this.options.max - this.options.min);
        const trackWidth = this.track.offsetWidth || this.options.width - 50;
        const thumbWidth = 11;
        this.thumb.style.left = `${ratio * (trackWidth - thumbWidth)}px`;

        if (this.valueDisplay) {
            this.valueDisplay.textContent = this.options.value;
        }
    }

    getValue() {
        return this.options.value;
    }

    setValue(value) {
        value = Math.max(this.options.min, Math.min(this.options.max, value));
        this.options.value = value;
        this._updateThumbPosition();
    }

    appendTo(parent) {
        if (typeof parent === 'string') {
            document.querySelector(parent).appendChild(this.element);
        } else {
            parent.appendChild(this.element);
        }
        // 트랙 크기 계산을 위해 다음 프레임에서 위치 업데이트
        requestAnimationFrame(() => this._updateThumbPosition());
        return this;
    }
}

/**
 * Windows 95 스타일 프로그레스바
 */
class RetroProgress {
    constructor(options = {}) {
        this.options = {
            value: options.value || 0,
            max: options.max || 100,
            width: options.width || 200,
            animated: options.animated || false,
        };

        this.element = null;
        this.bar = null;
        this._create();
    }

    _create() {
        this.element = document.createElement('div');
        this.element.className = 'win95-progress';
        this.element.style.width = `${this.options.width}px`;

        this.bar = document.createElement('div');
        this.bar.className = 'win95-progress-bar';

        this.element.appendChild(this.bar);
        this._updateBar();
    }

    _updateBar() {
        const percent = (this.options.value / this.options.max) * 100;
        this.bar.style.width = `${percent}%`;
    }

    getValue() {
        return this.options.value;
    }

    setValue(value) {
        this.options.value = Math.max(0, Math.min(this.options.max, value));
        this._updateBar();
    }

    increment(amount = 1) {
        this.setValue(this.options.value + amount);
    }

    appendTo(parent) {
        if (typeof parent === 'string') {
            document.querySelector(parent).appendChild(this.element);
        } else {
            parent.appendChild(this.element);
        }
        return this;
    }
}

window.RetroSlider = RetroSlider;
window.RetroProgress = RetroProgress;
