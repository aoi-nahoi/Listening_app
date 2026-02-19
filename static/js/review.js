// 復習機能のJavaScript

class ReviewManager {
    constructor() {
        this.currentUser = null;
        this.wrongQuestions = [];
        this.learningHistory = [];
        this.answerHistory = [];
        this.scoreChart = null;
        this.init();
    }

    async init() {
        await this.loadUserData();
        await this.loadWrongQuestions();
        await this.loadLearningHistory();
        await this.loadAnswerHistory();
        this.initScoreChart();
        this.updateSummaryStats();
        this.bindEvents();
    }

    async loadUserData() {
        try {
            const response = await fetch('/api/user/profile');
            if (response.ok) {
                this.currentUser = await response.json();
            }
        } catch (error) {
            console.error('ユーザーデータの読み込みに失敗しました:', error);
        }
    }

    async loadWrongQuestions() {
        try {
            const response = await fetch('/api/review/wrong-questions');
            if (response.ok) {
                const data = await response.json();
                if (data.error) {
                    console.error('APIエラー:', data.error);
                    this.showErrorMessage('間違えた問題の取得に失敗しました');
                } else {
                    this.wrongQuestions = data;
                    this.renderWrongQuestions();
                }
            } else {
                console.error('HTTPエラー:', response.status);
                this.showErrorMessage('間違えた問題の取得に失敗しました');
            }
        } catch (error) {
            console.error('間違えた問題の読み込みに失敗しました:', error);
            this.showErrorMessage('ネットワークエラーが発生しました');
        }
    }

    async loadLearningHistory() {
        try {
            const response = await fetch('/api/review/learning-history');
            if (response.ok) {
                this.learningHistory = await response.json();
                this.renderLearningHistory();
            }
        } catch (error) {
            console.error('学習履歴の読み込みに失敗しました:', error);
        }
    }

    async loadAnswerHistory() {
        try {
            const response = await fetch('/api/review/answer-history');
            if (response.ok) {
                this.answerHistory = await response.json();
                this.renderAnswerHistory();
            }
        } catch (error) {
            console.error('回答履歴の読み込みに失敗しました:', error);
        }
        }
    }

    renderWrongQuestions() {
        const container = document.getElementById('wrong-questions-list');
        
        if (this.wrongQuestions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-check-circle"></i>
                    <h5>素晴らしい！</h5>
                    <p>間違えた問題はありません。継続して学習を続けましょう！</p>
                </div>
            `;
            return;
        }

        const questionsHtml = this.wrongQuestions.map(question => `
            <div class="wrong-question-item fade-in" data-question-id="${question.id}">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h6 class="mb-2">
                            <i class="fas fa-question-circle me-2"></i>
                            ${this.escapeHtml(question.question_text)}
                        </h6>
                        <p class="mb-2 text-muted">
                            <small>
                                <i class="fas fa-clock me-1"></i>
                                間違えた日時: ${this.formatDate(question.wrong_date)}
                            </small>
                        </p>
                        <p class="mb-0">
                            <span class="badge bg-danger me-2">間違えた回数: ${question.wrong_count}</span>
                            <span class="badge bg-info">正解: ${this.escapeHtml(question.correct_answer)}</span>
                        </p>
                    </div>
                    <div class="col-md-4 text-end">
                        <button class="btn btn-warning btn-sm me-2" onclick="reviewManager.reviewQuestion(${question.id})">
                            <i class="fas fa-redo me-1"></i>復習
                        </button>
                        <button class="btn btn-outline-secondary btn-sm" onclick="reviewManager.showQuestionDetails(${question.id})">
                            <i class="fas fa-eye me-1"></i>詳細
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = questionsHtml;
    }

    renderLearningHistory() {
        const container = document.getElementById('learning-history');
        
        if (this.learningHistory.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <h5>学習履歴がありません</h5>
                    <p>学習を開始すると、ここに履歴が表示されます。</p>
                </div>
            `;
            return;
        }

        const historyHtml = this.learningHistory.map(entry => `
            <div class="history-item">
                <div class="row align-items-center">
                    <div class="col-md-6">
                        <strong>${this.escapeHtml(entry.content_title || '問題')}</strong>
                        <div class="history-date">${this.formatDate(entry.study_date)}</div>
                    </div>
                    <div class="col-md-3 text-center">
                        <span class="history-score score-${this.getScoreClass(entry.score)}">
                            ${entry.score || 'N/A'}
                        </span>
                    </div>
                    <div class="col-md-3 text-end">
                        <small class="text-muted">
                            <i class="fas fa-clock me-1"></i>
                            ${entry.time_spent || 0}分
                        </small>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = historyHtml;
    }

    renderAnswerHistory() {
        const container = document.getElementById('answer-history');
        
        if (this.answerHistory.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-clipboard-list"></i>
                    <h5>回答履歴がありません</h5>
                    <p>問題に回答すると、ここに履歴が表示されます。</p>
                </div>
            `;
            return;
        }

        const historyHtml = this.answerHistory.map(entry => `
            <div class="history-item">
                <div class="row align-items-center">
                    <div class="col-md-6">
                        <strong>${this.escapeHtml(entry.question_text)}</strong>
                        <div class="history-date">${this.formatDate(entry.answer_date)}</div>
                    </div>
                    <div class="col-md-3 text-center">
                        <span class="history-score ${entry.is_correct ? 'score-high' : 'score-low'}">
                            ${entry.is_correct ? '正解' : '不正解'}
                        </span>
                    </div>
                    <div class="col-md-3 text-end">
                        <small class="text-muted">
                            回答: ${this.escapeHtml(entry.user_answer)}
                        </small>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = historyHtml;
    }

    initScoreChart() {
        const ctx = document.getElementById('scoreChart').getContext('2d');
        
        // サンプルデータ（実際のAPIから取得したデータに置き換える）
        const sampleData = this.generateSampleScoreData();
        
        this.scoreChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sampleData.labels,
                datasets: [{
                    label: 'スコア推移',
                    data: sampleData.scores,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                }
            }
        });
    }

    generateSampleScoreData() {
        const labels = [];
        const scores = [];
        const today = new Date();
        
        for (let i = 6; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' }));
            scores.push(Math.floor(Math.random() * 40) + 60); // 60-100の範囲
        }
        
        return { labels, scores };
    }

    updateSummaryStats() {
        const safe = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };
        // 間違えた問題数
        safe('wrong-questions-count', this.wrongQuestions.length);
        // 総学習時間
        const totalStudyTime = this.learningHistory.reduce((total, entry) => total + (entry.time_spent || 0), 0);
        safe('study-time', totalStudyTime);
        // 正答率
        const correctAnswers = this.answerHistory.filter(entry => entry.is_correct).length;
        const totalAnswers = this.answerHistory.length;
        const accuracyRate = totalAnswers > 0 ? Math.round((correctAnswers / totalAnswers) * 100) : 0;
        safe('accuracy-rate', `${accuracyRate}%`);
        
        // 学習日数（study_date が null/undefined の場合はスキップ）
        const studyDates = this.learningHistory
            .map(entry => entry.study_date)
            .filter(Boolean)
            .map(s => (typeof s === 'string' && s.includes(' ') ? s.split(' ')[0] : s));
        const uniqueStudyDates = new Set(studyDates).size;
        safe('study-days', uniqueStudyDates);
    }

    async reviewQuestion(questionId) {
        try {
            const response = await fetch(`/api/review/question/${questionId}`);
            if (response.ok) {
                const question = await response.json();
                this.showReviewModal(question);
            }
        } catch (error) {
            console.error('問題の読み込みに失敗しました:', error);
        }
    }

    showReviewModal(question) {
        const modal = document.getElementById('reviewModal');
        const content = document.getElementById('review-question-content');
        
        content.innerHTML = `
            <div class="review-question">
                <h6 class="mb-3">問題を復習しましょう</h6>
                
                <div class="audio-player-container">
                    <audio controls class="w-100">
                        <source src="${question.audio_url}" type="audio/mpeg">
                        お使いのブラウザは音声再生をサポートしていません。
                    </audio>
                </div>
                
                <div class="question-details">
                    <p class="mb-3"><strong>問題文:</strong> ${this.escapeHtml(question.question_text)}</p>
                    <p class="mb-3"><strong>正解:</strong> ${this.escapeHtml(question.correct_answer)}</p>
                    
                    <div class="answer-options">
                        <h6 class="mb-2">選択肢:</h6>
                        <div class="answer-option" data-answer="A">
                            <strong>A.</strong> ${this.escapeHtml(question.option_a || '選択肢A')}
                        </div>
                        <div class="answer-option" data-answer="B">
                            <strong>B.</strong> ${this.escapeHtml(question.option_b || '選択肢B')}
                        </div>
                        <div class="answer-option" data-answer="C">
                            <strong>C.</strong> ${this.escapeHtml(question.option_c || '選択肢C')}
                        </div>
                        <div class="answer-option" data-answer="D">
                            <strong>D.</strong> ${this.escapeHtml(question.option_d || '選択肢D')}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 選択肢のクリックイベント
        const answerOptions = content.querySelectorAll('.answer-option');
        answerOptions.forEach(option => {
            option.addEventListener('click', () => {
                answerOptions.forEach(opt => opt.classList.remove('selected'));
                option.classList.add('selected');
            });
        });
        
        // 復習開始ボタンのイベント
        document.getElementById('start-review').onclick = () => {
            this.startReview(question.id);
        };
        
        // モーダルを表示
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }

    async startReview(questionId) {
        // 復習開始の処理
        try {
            const response = await fetch('/api/review/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question_id: questionId })
            });
            
            if (response.ok) {
                        // 復習詳細ページにリダイレクト
        window.location.href = `/review/${questionId}`;
            }
        } catch (error) {
            console.error('復習開始に失敗しました:', error);
        }
    }

    async showQuestionDetails(questionId) {
        try {
            const response = await fetch(`/api/review/question/${questionId}`);
            if (response.ok) {
                const details = await response.json();
                this.showDetailsModal(details);
            }
        } catch (error) {
            console.error('問題詳細の読み込みに失敗しました:', error);
        }
    }

    showDetailsModal(details) {
        // 詳細モーダルの表示（実装は省略）
        alert('詳細機能は開発中です');
    }

    bindEvents() {
        // 必要に応じてイベントリスナーを追加
    }

    showErrorMessage(message) {
        const container = document.getElementById('wrong-questions-list');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                    <button type="button" class="btn btn-sm btn-outline-danger ms-2" onclick="location.reload()">
                        <i class="fas fa-redo me-1"></i>再読み込み
                    </button>
                </div>
            `;
        }
    }

    // ユーティリティ関数
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        if (dateString == null || dateString === '') return '—';
        const date = new Date(dateString);
        if (Number.isNaN(date.getTime())) return '—';
        return date.toLocaleDateString('ja-JP', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    getScoreClass(score) {
        if (score >= 80) return 'high';
        if (score >= 60) return 'medium';
        return 'low';
    }
}

// ページ読み込み完了後に初期化
document.addEventListener('DOMContentLoaded', () => {
    window.reviewManager = new ReviewManager();
});
