/**
 * Windows 95 스타일 버튼 컴포넌트
 */

class RetroButton {
    constructor(options = {}) {
        this.options = {
            text: options.text || 'OK',
            width: options.width || null,
            disabled: options.disabled || false,
            isDefault: options.isDefault || false,
            onClick: options.onClick || null,
        };

        this.element = null;
        this._create();
    }

    _create() {
        this.element = document.createElement('button');
        this.element.className = 'win95-button';
        this.element.textContent = this.options.text;

        if (this.options.width) {
            this.element.style.minWidth = `${this.options.width}px`;
        }

        if (this.options.disabled) {
            this.element.disabled = true;
        }

        if (this.options.isDefault) {
            this.element.classList.add('default');
        }

        if (this.options.onClick) {
            this.element.addEventListener('click', this.options.onClick);
        }
    }

    setText(text) {
        this.options.text = text;
        this.element.textContent = text;
    }

    setDisabled(disabled) {
        this.options.disabled = disabled;
        this.element.disabled = disabled;
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

/**
 * Windows 95 스타일 다이얼로그
 */
class RetroDialog {
    constructor(options = {}) {
        this.options = {
            title: options.title || 'Dialog',
            message: options.message || '',
            type: options.type || 'info', // info, warning, error, question
            buttons: options.buttons || ['OK'],
            onButton: options.onButton || null,
        };

        this.overlay = null;
        this.window = null;
        this._create();
    }

    _create() {
        // 오버레이
        this.overlay = document.createElement('div');
        this.overlay.className = 'win95-dialog-overlay';

        // 다이얼로그 윈도우
        const dialogEl = document.createElement('div');
        dialogEl.className = 'win95-window win95-dialog';

        // 타이틀바
        const titlebar = document.createElement('div');
        titlebar.className = 'win95-titlebar';
        titlebar.innerHTML = `
            <span class="win95-titlebar-title">${this.options.title}</span>
        `;

        // 콘텐츠
        const content = document.createElement('div');
        content.className = 'win95-dialog-content';
        content.innerHTML = `
            <div class="win95-dialog-icon">${this._getIcon()}</div>
            <div class="win95-dialog-message">${this.options.message}</div>
        `;

        // 버튼 영역
        const buttons = document.createElement('div');
        buttons.className = 'win95-dialog-buttons';

        this.options.buttons.forEach((btnText, index) => {
            const btn = new RetroButton({
                text: btnText,
                isDefault: index === 0,
                onClick: () => {
                    if (this.options.onButton) {
                        this.options.onButton(btnText, index);
                    }
                    this.close();
                }
            });
            btn.appendTo(buttons);
        });

        // 조립
        dialogEl.appendChild(titlebar);
        dialogEl.appendChild(content);
        dialogEl.appendChild(buttons);
        this.overlay.appendChild(dialogEl);
    }

    _getIcon() {
        const icons = {
            info: 'i',
            warning: '!',
            error: 'X',
            question: '?'
        };
        return `<span style="font-size: 24px; font-weight: bold; color: ${this._getIconColor()}">${icons[this.options.type] || 'i'}</span>`;
    }

    _getIconColor() {
        const colors = {
            info: '#000080',
            warning: '#808000',
            error: '#800000',
            question: '#008000'
        };
        return colors[this.options.type] || '#000080';
    }

    show() {
        document.body.appendChild(this.overlay);
        return this;
    }

    close() {
        this.overlay.remove();
    }

    static alert(message, title = 'Alert') {
        return new RetroDialog({
            title,
            message,
            type: 'info',
            buttons: ['OK']
        }).show();
    }

    static confirm(message, title = 'Confirm') {
        return new Promise((resolve) => {
            new RetroDialog({
                title,
                message,
                type: 'question',
                buttons: ['OK', 'Cancel'],
                onButton: (btn) => resolve(btn === 'OK')
            }).show();
        });
    }
}

window.RetroButton = RetroButton;
window.RetroDialog = RetroDialog;
