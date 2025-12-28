/**
 * Windows 95 스타일 윈도우 컴포넌트
 */

class RetroWindow {
    constructor(options = {}) {
        this.options = {
            title: options.title || 'Window',
            width: options.width || 400,
            height: options.height || 300,
            x: options.x || 100,
            y: options.y || 100,
            resizable: options.resizable !== false,
            minimizable: options.minimizable !== false,
            maximizable: options.maximizable !== false,
            closable: options.closable !== false,
            content: options.content || '',
            onClose: options.onClose || null,
            onMinimize: options.onMinimize || null,
            onMaximize: options.onMaximize || null,
        };

        this.element = null;
        this.titlebar = null;
        this.contentArea = null;
        this.isMaximized = false;
        this.isMinimized = false;
        this.isDragging = false;
        this.dragOffset = { x: 0, y: 0 };
        this.originalBounds = null;

        this._create();
        this._bindEvents();
    }

    _create() {
        // 윈도우 컨테이너
        this.element = document.createElement('div');
        this.element.className = 'win95-window';
        this.element.style.cssText = `
            position: absolute;
            left: ${this.options.x}px;
            top: ${this.options.y}px;
            width: ${this.options.width}px;
            min-width: 200px;
            min-height: 100px;
        `;

        // 타이틀바
        this.titlebar = document.createElement('div');
        this.titlebar.className = 'win95-titlebar';
        this.titlebar.innerHTML = `
            <span class="win95-titlebar-title">${this.options.title}</span>
            <div class="win95-titlebar-buttons">
                ${this.options.minimizable ? '<button class="win95-titlebar-btn win95-btn-minimize" title="Minimize"></button>' : ''}
                ${this.options.maximizable ? '<button class="win95-titlebar-btn win95-btn-maximize" title="Maximize"></button>' : ''}
                ${this.options.closable ? '<button class="win95-titlebar-btn win95-btn-close" title="Close"></button>' : ''}
            </div>
        `;

        // 콘텐츠 영역
        this.contentArea = document.createElement('div');
        this.contentArea.className = 'win95-window-content';
        this.contentArea.style.height = `${this.options.height - 26}px`;
        this.contentArea.style.overflow = 'auto';

        if (typeof this.options.content === 'string') {
            this.contentArea.innerHTML = this.options.content;
        } else if (this.options.content instanceof HTMLElement) {
            this.contentArea.appendChild(this.options.content);
        }

        // 조립
        this.element.appendChild(this.titlebar);
        this.element.appendChild(this.contentArea);
    }

    _bindEvents() {
        // 타이틀바 드래그
        this.titlebar.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('win95-titlebar-btn')) return;
            this.isDragging = true;
            this.dragOffset = {
                x: e.clientX - this.element.offsetLeft,
                y: e.clientY - this.element.offsetTop
            };
            this.element.style.zIndex = RetroWindow.getNextZIndex();
        });

        document.addEventListener('mousemove', (e) => {
            if (!this.isDragging) return;
            this.element.style.left = `${e.clientX - this.dragOffset.x}px`;
            this.element.style.top = `${e.clientY - this.dragOffset.y}px`;
        });

        document.addEventListener('mouseup', () => {
            this.isDragging = false;
        });

        // 버튼 이벤트
        const minimizeBtn = this.titlebar.querySelector('.win95-btn-minimize');
        const maximizeBtn = this.titlebar.querySelector('.win95-btn-maximize');
        const closeBtn = this.titlebar.querySelector('.win95-btn-close');

        if (minimizeBtn) {
            minimizeBtn.addEventListener('click', () => this.minimize());
        }
        if (maximizeBtn) {
            maximizeBtn.addEventListener('click', () => this.toggleMaximize());
        }
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }

        // 포커스
        this.element.addEventListener('mousedown', () => {
            this.element.style.zIndex = RetroWindow.getNextZIndex();
        });
    }

    minimize() {
        this.isMinimized = true;
        this.element.style.display = 'none';
        if (this.options.onMinimize) {
            this.options.onMinimize(this);
        }
    }

    restore() {
        this.isMinimized = false;
        this.element.style.display = '';
        this.element.style.zIndex = RetroWindow.getNextZIndex();
    }

    toggleMaximize() {
        if (this.isMaximized) {
            // 복원
            this.element.style.left = `${this.originalBounds.x}px`;
            this.element.style.top = `${this.originalBounds.y}px`;
            this.element.style.width = `${this.originalBounds.width}px`;
            this.contentArea.style.height = `${this.originalBounds.height - 26}px`;
            this.isMaximized = false;
        } else {
            // 최대화
            this.originalBounds = {
                x: this.element.offsetLeft,
                y: this.element.offsetTop,
                width: this.element.offsetWidth,
                height: this.element.offsetHeight
            };
            this.element.style.left = '0';
            this.element.style.top = '0';
            this.element.style.width = '100%';
            this.contentArea.style.height = `calc(100vh - 26px)`;
            this.isMaximized = true;
        }

        if (this.options.onMaximize) {
            this.options.onMaximize(this, this.isMaximized);
        }
    }

    close() {
        if (this.options.onClose) {
            const result = this.options.onClose(this);
            if (result === false) return;
        }
        this.element.remove();
    }

    setTitle(title) {
        this.options.title = title;
        this.titlebar.querySelector('.win95-titlebar-title').textContent = title;
    }

    setContent(content) {
        if (typeof content === 'string') {
            this.contentArea.innerHTML = content;
        } else if (content instanceof HTMLElement) {
            this.contentArea.innerHTML = '';
            this.contentArea.appendChild(content);
        }
    }

    appendTo(parent) {
        if (typeof parent === 'string') {
            document.querySelector(parent).appendChild(this.element);
        } else {
            parent.appendChild(this.element);
        }
        return this;
    }

    static zIndex = 100;
    static getNextZIndex() {
        return ++RetroWindow.zIndex;
    }
}

window.RetroWindow = RetroWindow;
