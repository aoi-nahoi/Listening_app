// 英語リスニングアプリ メインJavaScript

// グローバル設定
const APP_CONFIG = {
    API_BASE_URL: '',
    DEBUG_MODE: true,
    ANIMATION_DURATION: 300
};

// ユーティリティ関数
const Utils = {
    // ログ出力
    log: function(message, type = 'info') {
        if (APP_CONFIG.DEBUG_MODE) {
            const timestamp = new Date().toLocaleTimeString();
            console.log(`[${timestamp}] ${type.toUpperCase()}: ${message}`);
        }
    },

    // 要素の表示/非表示切り替え
    toggleElement: function(elementId, show = true) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = show ? 'block' : 'none';
        }
    },

    // 要素の有効/無効切り替え
    toggleDisabled: function(elementId, disabled = false) {
        const element = document.getElementById(elementId);
        if (element) {
            element.disabled = disabled;
        }
    },

    // 成功メッセージ表示
    showSuccess: function(message, duration = 3000) {
        this.showMessage(message, 'success', duration);
    },

    // エラーメッセージ表示
    showError: function(message, duration = 5000) {
        this.showMessage(message, 'danger', duration);
    },

    // 情報メッセージ表示
    showInfo: function(message, duration = 3000) {
        this.showMessage(message, 'info', duration);
    },

    // メッセージ表示（共通）
    showMessage: function(message, type = 'info', duration = 3000) {
        const alertContainer = document.createElement('div');
        alertContainer.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertContainer.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        `;
        
        alertContainer.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertContainer);
        
        // 自動で非表示
        setTimeout(() => {
            if (alertContainer.parentNode) {
                alertContainer.remove();
            }
        }, duration);
    },

    // 数値のフォーマット
    formatNumber: function(number, decimals = 0) {
        return new Intl.NumberFormat('ja-JP', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(number);
    },

    // 日付のフォーマット
    formatDate: function(date, format = 'YYYY-MM-DD') {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day);
    },

    // 文字列の長さチェック
    validateLength: function(str, min, max) {
        const length = str.trim().length;
        return length >= min && length <= max;
    },

    // メールアドレスのバリデーション
    validateEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    // パスワードの強度チェック
    validatePasswordStrength: function(password) {
        const checks = {
            length: password.length >= 8,
            lowercase: /[a-z]/.test(password),
            uppercase: /[A-Z]/.test(password),
            number: /\d/.test(password),
            special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
        };
        
        const score = Object.values(checks).filter(Boolean).length;
        
        return {
            score: score,
            strong: score >= 4,
            medium: score >= 3,
            weak: score < 3,
            checks: checks
        };
    }
};

// フォームバリデーション
const FormValidator = {
    // 必須フィールドチェック
    required: function(value) {
        return value && value.trim().length > 0;
    },

    // 最小文字数チェック
    minLength: function(value, min) {
        return value && value.length >= min;
    },

    // 最大文字数チェック
    maxLength: function(value, max) {
        return value && value.length <= max;
    },

    // パターンマッチチェック
    pattern: function(value, regex) {
        return regex.test(value);
    },

    // フォーム全体のバリデーション
    validateForm: function(formElement) {
        const inputs = formElement.querySelectorAll('input, select, textarea');
        let isValid = true;
        const errors = [];

        inputs.forEach(input => {
            const value = input.value;
            const rules = input.dataset.validation ? JSON.parse(input.dataset.validation) : {};

            // 必須チェック
            if (rules.required && !this.required(value)) {
                this.showFieldError(input, 'このフィールドは必須です');
                isValid = false;
                errors.push(`${input.name}: 必須フィールド`);
            }

            // 最小文字数チェック
            if (rules.minLength && !this.minLength(value, rules.minLength)) {
                this.showFieldError(input, `${rules.minLength}文字以上で入力してください`);
                isValid = false;
                errors.push(`${input.name}: 最小文字数不足`);
            }

            // 最大文字数チェック
            if (rules.maxLength && !this.maxLength(value, rules.maxLength)) {
                this.showFieldError(input, `${rules.maxLength}文字以下で入力してください`);
                isValid = false;
                errors.push(`${input.name}: 最大文字数超過`);
            }

            // パターンチェック
            if (rules.pattern && !this.pattern(value, new RegExp(rules.pattern))) {
                this.showFieldError(input, rules.patternMessage || '入力形式が正しくありません');
                isValid = false;
                errors.push(`${input.name}: パターンマッチ失敗`);
            }

            // エラーがない場合はエラー表示をクリア
            if (isValid) {
                this.clearFieldError(input);
            }
        });

        return { isValid, errors };
    },

    // フィールドエラー表示
    showFieldError: function(input, message) {
        this.clearFieldError(input);
        
        input.classList.add('is-invalid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        input.parentNode.appendChild(errorDiv);
    },

    // フィールドエラークリア
    clearFieldError: function(input) {
        input.classList.remove('is-invalid');
        
        const errorDiv = input.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
};

// UI操作
const UI = {
    // ローディング表示
    showLoading: function(elementId, text = '読み込み中...') {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">${text}</span>
                    </div>
                    <p class="text-muted">${text}</p>
                </div>
            `;
        }
    },

    // ローディング非表示
    hideLoading: function(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = '';
        }
    },

    // モーダル表示
    showModal: function(modalId) {
        const modal = new bootstrap.Modal(document.getElementById(modalId));
        modal.show();
    },

    // モーダル非表示
    hideModal: function(modalId) {
        const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (modal) {
            modal.hide();
        }
    },

    // タブ切り替え
    switchTab: function(tabId) {
        const tab = new bootstrap.Tab(document.querySelector(`[data-bs-target="#${tabId}"]`));
        tab.show();
    },

    // ツールチップ初期化
    initTooltips: function() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },

    // ポップオーバー初期化
    initPopovers: function() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
};

// ページ読み込み完了時の初期化
document.addEventListener('DOMContentLoaded', function() {
    Utils.log('アプリケーション初期化開始');
    
    // ツールチップとポップオーバーの初期化
    UI.initTooltips();
    UI.initPopovers();
    
    // フォームバリデーションの設定
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const validation = FormValidator.validateForm(this);
            if (!validation.isValid) {
                e.preventDefault();
                Utils.showError('入力内容に誤りがあります。確認してください。');
                Utils.log(`フォームバリデーションエラー: ${validation.errors.join(', ')}`, 'error');
            }
        });
    });
    
    // アニメーション要素の監視
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.card, .btn').forEach(el => {
        observer.observe(el);
    });
    
    Utils.log('アプリケーション初期化完了');
});

// グローバルエラーハンドリング
window.addEventListener('error', function(e) {
    Utils.log(`JavaScriptエラー: ${e.message}`, 'error');
    Utils.showError('予期しないエラーが発生しました。ページを再読み込みしてください。');
});

// 未処理のPromise拒否のハンドリング
window.addEventListener('unhandledrejection', function(e) {
    Utils.log(`Promise拒否: ${e.reason}`, 'error');
    Utils.showError('通信エラーが発生しました。');
});

// エクスポート
window.AppUtils = Utils;
window.FormValidator = FormValidator;
window.UI = UI;
