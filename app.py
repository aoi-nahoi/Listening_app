from flask import Flask, request, jsonify, redirect, url_for, render_template, flash, session
from flask_migrate import Migrate
from flask_login import current_user, login_required, login_user, logout_user, LoginManager
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
import os
import io
import logging
import time
from datetime import datetime, timedelta
from ml_recommendations import recommend_content  # 推薦機能をインポート
from google.cloud import speech
from google.cloud import speech_v1p1beta1 as speech_beta
import re
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _ensure_gcp_credentials():
    """
    Render 等のクラウドでは ADC が無いため、
    環境変数 GOOGLE_CREDENTIALS_JSON にサービスアカウント JSON 文字列を設定可能にする。
    設定されている場合、一時ファイルに書き出して GOOGLE_APPLICATION_CREDENTIALS をセットする。
    """
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON") or os.environ.get("GCP_CREDENTIALS_JSON")
    if not credentials_json:
        return
    try:
        import tempfile
        import json
        # 有効な JSON か確認
        json.loads(credentials_json)
        fd, path = tempfile.mkstemp(suffix=".json", prefix="gcp_credentials_")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(credentials_json)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
            logger.info("GCP credentials set from GOOGLE_CREDENTIALS_JSON environment variable.")
        except Exception:
            os.close(fd)
            if os.path.exists(path):
                os.unlink(path)
            raise
    except json.JSONDecodeError as e:
        logger.warning(f"GOOGLE_CREDENTIALS_JSON is not valid JSON: {e}")

app = Flask(__name__)

# 設定
import os

# データベース設定（環境変数から取得、デフォルトはSQLite）
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # RenderやHerokuなどの本番環境用（PostgreSQL）
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # 開発環境用（SQLite）
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'listening.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['UPLOAD_FOLDER'] = './static/audio'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')  # 環境変数から取得

# データベース初期化
db.init_app(app)

# Flask-Login の設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'このページにアクセスするにはログインが必要です。'

# Flask-Migrate の設定
migrate = Migrate(app, db)

from models import User, Question, LearningLog, TestResult

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 認証関連のルート
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('ログインしました！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('ユーザー名またはパスワードが正しくありません。', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # バリデーション
        if not username or not email or not password:
            flash('すべてのフィールドを入力してください。', 'error')
        elif password != confirm_password:
            flash('パスワードが一致しません。', 'error')
        elif User.query.filter_by(username=username).first():
            flash('このユーザー名は既に使用されています。', 'error')
        elif User.query.filter_by(email=email).first():
            flash('このメールアドレスは既に登録されています。', 'error')
        else:
            # 新規ユーザー作成
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            
            flash('アカウントが作成されました。ログインしてください。', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました。', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    # ユーザーの学習統計を取得
    learning_logs = LearningLog.query.filter_by(user_id=current_user.id).all()
    total_questions = len(learning_logs)
    correct_answers = sum(1 for log in learning_logs if log.score == 1)
    accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # 最近の学習履歴
    recent_logs = LearningLog.query.filter_by(user_id=current_user.id).order_by(LearningLog.id.desc()).limit(5).all()

    # 登録日（User.created_at が無い既存ユーザーは '—'）
    registered_at = '—'
    if getattr(current_user, 'created_at', None):
        try:
            registered_at = current_user.created_at.strftime('%Y年%m月%d日')
        except Exception:
            pass

    return render_template('profile.html',
                        user=current_user,
                        registered_at=registered_at,
                        total_questions=total_questions,
                        correct_answers=correct_answers,
                        accuracy=accuracy,
                        recent_logs=recent_logs)

@app.route('/dashboard')
@login_required
def dashboard():
    # 最近の問題を取得
    recent_questions = Question.query.filter_by(is_public=True).order_by(Question.id.desc()).limit(3).all()

    # ユーザーの学習ログ（進捗サマリー用）
    learning_logs = LearningLog.query.filter_by(user_id=current_user.id).all()
    total_score = sum(log.score or 0 for log in learning_logs)

    # 過去7日間の集計
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    logs_this_week = [log for log in learning_logs if log.created_at and log.created_at >= week_ago]
    days_this_week = len(set(log.created_at.date() for log in logs_this_week)) if logs_this_week else 0
    minutes_this_week = sum(log.time_spent or 0 for log in logs_this_week)
    minutes_this_week = int(round(minutes_this_week))

    # 連続学習日数
    learning_streak = calculate_learning_streak(learning_logs)

    return render_template('dashboard.html',
                        user=current_user,
                        recent_questions=recent_questions,
                        total_score=total_score,
                        days_this_week=days_this_week,
                        minutes_this_week=minutes_this_week,
                        learning_streak=learning_streak)

# メイン学習系のルート
@app.route('/questions')
@login_required
def questions():
    """問題一覧ページ"""
    return render_template('questions.html')

@app.route('/learn/<int:question_id>')
@login_required
def learn(question_id):
    """問題学習ページ"""
    question = Question.query.get_or_404(question_id)
    # 音声URL: DBには ./static/audio/ や フルパス が入る場合があるため、配信用URLに正規化
    raw = question.audio_url or ''
    if raw.startswith('/') or raw.startswith('http'):
        audio_src = raw
    else:
        audio_src = url_for('static', filename='audio/' + raw.replace('\\', '/').split('/')[-1])
    return render_template('learn.html', question=question, audio_src=audio_src)

@app.route('/upload')
@login_required
def upload():
    """音声アップロードページ"""
    return render_template('upload.html')


# 音声認識（MP3/WAV対応・フォーマットに応じた最適設定）
def transcribe_audio(audio_file_path):
    _ensure_gcp_credentials()
    ext = os.path.splitext(audio_file_path)[1].lower()
    with io.open(audio_file_path, "rb") as f:
        content = f.read()

    # MP3: v1p1beta1 のみ対応。正しいエンコーディング指定で高速・確実に認識
    if ext == ".mp3":
        client = speech_beta.SpeechClient()
        config = speech_beta.types.RecognitionConfig(
            encoding=speech_beta.types.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=44100,
            language_code="en-US",
        )
        audio = speech_beta.types.RecognitionAudio(content=content)
        response = client.recognize(config=config, audio=audio)
    # WAV: ヘッダから自動判定させる（サンプルレート等をAPIに任せる）
    elif ext == ".wav":
        client = speech_beta.SpeechClient()
        config = speech_beta.types.RecognitionConfig(
            encoding=speech_beta.types.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
            language_code="en-US",
        )
        audio = speech_beta.types.RecognitionAudio(content=content)
        response = client.recognize(config=config, audio=audio)
    else:
        # その他（未対応形式は LINEAR16 16kHz として扱う）
        client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )
        audio = speech.RecognitionAudio(content=content)
        response = client.recognize(config=config, audio=audio)

    if not response.results:
        return ""
    transcript = " ".join(
        result.alternatives[0].transcript for result in response.results
    )
    return transcript


import random

def generate_question(transcript: str):
    """
    文字起こしテキストから穴埋め問題を自動生成する。
    
    改良点：
    1. 英語・日本語どちらも対応
    2. 大文字小文字を無視して置換
    3. 複数候補からランダムに選択
    
    Returns: (question_text, correct_answer)
    """
    if not transcript:
        return ("Listen to the audio and answer the question.", "")

    # 単語を抽出（英単語 + 日本語の連続文字列）
    words = re.findall(r"[A-Za-z']+|[一-龥ぁ-んァ-ン]+", transcript)

    # 4文字以上の単語を候補にする
    candidates = [word for word in words if len(word) >= 4]

    # 候補がなければ末尾の単語を使用
    if not candidates and words:
        candidates = [words[-1]]

    if not candidates:
        return (transcript, "")

    # 複数候補からランダムに選択
    target_word = random.choice(candidates)

    # 単語を穴埋めに置換（大文字小文字を無視）
    pattern = re.compile(re.escape(target_word), re.IGNORECASE)
    question_text = pattern.sub("____", transcript, count=1)

    correct_answer = target_word
    return question_text, correct_answer


# 音声アップロード用エンドポイント（/upload_audio と /api/upload_audio の両方に対応）
@app.route('/upload_audio', methods=['POST'])
@app.route('/api/upload_audio', methods=['POST'])
@login_required
def upload_audio():
    # フォームの name="audio_file" と name="file" の両方を受け付ける
    file = request.files.get('audio_file') or request.files.get('file')
    if not file:
        logger.error('No file part in the request')
        return jsonify({'error': 'No file part in the request'}), 400
    if file.filename == '':
        logger.warning('No file selected for uploading')
        return jsonify({'error': 'No file selected for uploading'}), 400

    try:
        t0 = time.perf_counter()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        t_save = time.perf_counter() - t0
        logger.info(f'[upload] ファイル保存: {t_save:.2f}s')

        t1 = time.perf_counter()
        transcript = transcribe_audio(filepath)
        t_transcribe = time.perf_counter() - t1
        logger.info(f'[upload] 音声認識(Speech-to-Text): {t_transcribe:.2f}s')

        transcript_path = os.path.splitext(filepath)[0] + '.txt'
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript)

        t2 = time.perf_counter()
        question_text, correct_answer = generate_question(transcript)
        t_generate = time.perf_counter() - t2
        logger.info(f'[upload] 穴埋め問題生成: {t_generate:.2f}s')

        is_public = request.form.get('is_public', 'true').lower() == 'true'

        t3 = time.perf_counter()
        question = Question(
            audio_url=filepath,
            question_text=question_text,
            correct_answer=correct_answer,
            uploaded_by=current_user.id,
            is_public=is_public
        )
        db.session.add(question)
        db.session.commit()
        t_db = time.perf_counter() - t3
        logger.info(f'[upload] DB保存: {t_db:.2f}s')

        total = time.perf_counter() - t0
        logger.info(f'[upload] 合計: {total:.2f}s (保存={t_save:.2f}, 音声認識={t_transcribe:.2f}, 問題生成={t_generate:.2f}, DB={t_db:.2f})')
        return jsonify({
            'message': 'File uploaded successfully',
            'file_path': filepath,
            'transcript_path': transcript_path,
            'question_id': question.id,
        }), 200
    except Exception as e:
        db.session.rollback()
        err_msg = str(e)
        logger.error(f'Failed to save file: {err_msg}')
        if "credentials" in err_msg.lower() or "GOOGLE_APPLICATION_CREDENTIALS" in err_msg:
            error_user = (
                "音声認識の認証が設定されていません。"
                "Render の Environment で GOOGLE_CREDENTIALS_JSON にサービスアカウントの JSON を設定してください。"
            )
            return jsonify({'error': error_user}), 500
        return jsonify({'error': f'Failed to upload file: {err_msg}'}), 500


# リスニング問題を取得 (ランダム + 公開限定)
@app.route('/get_question', methods=['GET'])
def get_question():
    question = Question.query.filter_by(is_public=True).order_by(db.func.random()).first()
    if question:
        return jsonify({
            'id': question.id,
            'audio_url': question.audio_url,
            'question_text': question.question_text
        })
    else:
        logger.warning('No questions available')
        return jsonify({'error': 'No questions available'}), 404



# 公開問題一覧を取得
@app.route('/api/questions/public')
@login_required
def get_public_questions():
    """公開されている問題一覧を取得"""
    try:
        questions = Question.query.filter_by(is_public=True).all()
        result = []
        
        for q in questions:
            # アップローダー情報を取得
            uploader = User.query.get(q.uploaded_by) if q.uploaded_by else None
            
            question_data = {
                'id': q.id,
                'question_text': q.question_text,
                'difficulty': q.difficulty,
                'category': q.category,
                'created_at': q.created_at.isoformat() if q.created_at else None,
                'play_count': q.play_count or 0,
                'avg_score': q.avg_score or 0,
                'uploader': {
                    'username': uploader.username if uploader else 'Unknown'
                } if uploader else None
            }
            result.append(question_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f'Failed to get public questions: {str(e)}')
        return jsonify({'error': 'Failed to get questions'}), 500

# 回答の提出と採点
@app.route('/api/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    """回答を提出して採点する"""
    data = request.json
    if not data or 'question_id' not in data or 'user_answer' not in data:
        return jsonify({'error': 'Invalid input data'}), 400

    question_id = data.get('question_id')
    user_answer = data.get('user_answer')

    question = Question.query.get(question_id)
    if not question:
        return jsonify({'error': 'Question not found'}), 404

    # 採点処理
    is_correct = user_answer.strip().lower() == question.correct_answer.lower()
    score = 1 if is_correct else 0

    # 学習ログに記録
    try:
        log = LearningLog(
            user_id=current_user.id,
            content_id=question_id,
            question_id=question_id,
            user_answer=user_answer,
            score=score
        )
        db.session.add(log)
        db.session.commit()
        # 再生回数は Question にカラムが無いため更新しない（必要なら別途集計）

    except Exception as e:
        db.session.rollback()
        logger.error(f'Failed to log learning progress: {str(e)}')
        return jsonify({'error': 'Failed to log progress'}), 500

    return jsonify({
        'is_correct': is_correct,
        'score': score,
        'user_answer': user_answer,
        'correct_answer': question.correct_answer,
        'explanation': f'正解は「{question.correct_answer}」です。'
    })

# 学習ログの記録
@app.route('/api/log_learning', methods=['POST'])
@login_required
def log_learning():
    """学習結果を記録する"""
    data = request.json
    if not data or 'question_id' not in data:
        return jsonify({'error': 'Invalid input data'}), 400

    try:
        log = LearningLog(
            user_id=current_user.id,
            content_id=data.get('question_id'),
            question_id=data.get('question_id'),
            user_answer=data.get('user_answer', ''),
            score=data.get('score', 0)
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Failed to log learning: {str(e)}')
        return jsonify({'error': 'Failed to log learning'}), 500

# 推奨コンテンツページ
@app.route('/recommendations')
@login_required
def recommendations():
    """推奨コンテンツページ"""
    return render_template('recommendations.html')

# ユーザー統計の取得
@app.route('/api/user/stats')
@login_required
def get_user_stats():
    """ユーザーの学習統計を取得"""
    try:
        # 学習ログを取得
        logs = LearningLog.query.filter_by(user_id=current_user.id).all()
        
        if not logs:
            return jsonify({
                'total_questions': 0,
                'correct_rate': 0,
                'avg_score': 0,
                'learning_streak': 0
            })
        
        # 統計を計算
        total_questions = len(logs)
        correct_answers = sum(1 for log in logs if log.score == 1)
        correct_rate = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        avg_score = sum(log.score or 0 for log in logs) / total_questions if total_questions > 0 else 0
        
        # 連続学習日数を計算（簡易版）
        learning_streak = calculate_learning_streak(logs)
        
        return jsonify({
            'total_questions': total_questions,
            'correct_rate': round(correct_rate, 1),
            'avg_score': round(avg_score, 1),
            'learning_streak': learning_streak
        })
        
    except Exception as e:
        logger.error(f'Failed to get user stats: {str(e)}')
        return jsonify({'error': 'Failed to get stats'}), 500

# 学習履歴の取得
@app.route('/api/user/learning-history')
@login_required
def get_learning_history():
    """ユーザーの学習履歴を取得"""
    try:
        # 学習ログと問題情報を結合して取得
        logs = db.session.query(LearningLog, Question).join(
            Question, LearningLog.question_id == Question.id
        ).filter(
            LearningLog.user_id == current_user.id
        ).order_by(LearningLog.created_at.desc()).all()
        
        result = []
        for log, question in logs:
            log_data = {
                'id': log.id,
                'question_id': log.question_id,
                'user_answer': log.user_answer,
                'score': log.score,
                'created_at': log.created_at.isoformat() if log.created_at else None,
                'category': question.category,
                'difficulty': question.difficulty
            }
            result.append(log_data)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'Failed to get learning history: {str(e)}')
        return jsonify({'error': 'Failed to get history'}), 500

# 推奨コンテンツの取得
@app.route('/api/recommendations')
@login_required
def get_recommendations():
    """ユーザーに推奨するコンテンツを取得"""
    try:
        # ユーザーの学習履歴を分析
        user_profile = analyze_user_profile(current_user.id)
        
        # 推奨問題を取得
        recommended_questions = get_recommended_questions(user_profile)
        
        return jsonify(recommended_questions)
        
    except Exception as e:
        logger.error(f'Failed to get recommendations: {str(e)}')
        return jsonify({'error': 'Failed to get recommendations'}), 500

# ユーザープロファイルの分析
def analyze_user_profile(user_id):
    """ユーザーの学習プロファイルを分析"""
    try:
        logs = LearningLog.query.filter_by(user_id=user_id).all()
        
        if not logs:
            return {
                'level': 'beginner',
                'strengths': [],
                'weaknesses': [],
                'preferred_categories': [],
                'preferred_difficulty': 'easy'
            }
        
        # 分野別の正答率を計算
        category_stats = {}
        difficulty_stats = {}
        
        for log in logs:
            question = Question.query.get(log.question_id)
            if question:
                # カテゴリ統計
                if question.category:
                    if question.category not in category_stats:
                        category_stats[question.category] = {'total': 0, 'correct': 0}
                    category_stats[question.category]['total'] += 1
                    category_stats[question.category]['correct'] += log.score or 0
                
                # 難易度統計
                if question.difficulty:
                    if question.difficulty not in difficulty_stats:
                        difficulty_stats[question.difficulty] = {'total': 0, 'correct': 0}
                    difficulty_stats[question.difficulty]['total'] += 1
                    difficulty_stats[question.difficulty]['correct'] += log.score or 0
        
        # 得意・不得意分野を特定
        strengths = []
        weaknesses = []
        for category, stats in category_stats.items():
            accuracy = stats['correct'] / stats['total']
            if accuracy >= 0.7 and stats['total'] >= 3:
                strengths.append(category)
            elif accuracy < 0.5 and stats['total'] >= 3:
                weaknesses.append(category)
        
        # 推奨難易度を決定
        total_questions = len(logs)
        if total_questions < 5:
            preferred_difficulty = 'easy'
        elif total_questions < 15:
            preferred_difficulty = 'medium'
        else:
            # 最近の正答率に基づいて難易度を調整
            recent_logs = logs[-10:]  # 最近10問
            recent_accuracy = sum(log.score or 0 for log in recent_logs) / len(recent_logs)
            
            if recent_accuracy >= 0.8:
                preferred_difficulty = 'hard'
            elif recent_accuracy >= 0.6:
                preferred_difficulty = 'medium'
            else:
                preferred_difficulty = 'easy'
        
        return {
            'level': 'beginner' if total_questions < 10 else 'intermediate' if total_questions < 30 else 'advanced',
            'strengths': strengths,
            'weaknesses': weaknesses,
            'preferred_categories': list(category_stats.keys()),
            'preferred_difficulty': preferred_difficulty,
            'total_questions': total_questions
        }
        
    except Exception as e:
        logger.error(f'Failed to analyze user profile: {str(e)}')
        return {
            'level': 'beginner',
            'strengths': [],
            'weaknesses': [],
            'preferred_categories': [],
            'preferred_difficulty': 'easy'
        }

# 推奨問題の取得
def get_recommended_questions(user_profile):
    """ユーザープロファイルに基づいて推奨問題を取得"""
    try:
        recommendations = []
        
        # 改善が必要な分野の問題を優先的に推奨
        if user_profile['weaknesses']:
            for category in user_profile['weaknesses']:
                questions = Question.query.filter_by(
                    is_public=True,
                    category=category,
                    difficulty=user_profile['preferred_difficulty']
                ).limit(2).all()
                
                for question in questions:
                    recommendation = create_recommendation(question, user_profile, 'weakness_improvement')
                    recommendations.append(recommendation)
        
        # 得意分野の次のレベルを推奨
        if user_profile['strengths']:
            for category in user_profile['strengths']:
                # 得意分野では少し難しい問題を推奨
                next_difficulty = get_next_difficulty(user_profile['preferred_difficulty'])
                questions = Question.query.filter_by(
                    is_public=True,
                    category=category,
                    difficulty=next_difficulty
                ).limit(1).all()
                
                for question in questions:
                    recommendation = create_recommendation(question, user_profile, 'skill_advancement')
                    recommendations.append(recommendation)
        
        # 新しい分野を探索
        all_categories = ['conversation', 'news', 'story', 'academic']
        unexplored_categories = [cat for cat in all_categories if cat not in user_profile['preferred_categories']]
        
        if unexplored_categories:
            for category in unexplored_categories[:2]:
                questions = Question.query.filter_by(
                    is_public=True,
                    category=category,
                    difficulty='easy'  # 新しい分野は初級から
                ).limit(1).all()
                
                for question in questions:
                    recommendation = create_recommendation(question, user_profile, 'exploration')
                    recommendations.append(recommendation)
        
        # 推奨数が足りない場合は、適切な難易度の問題を追加
        if len(recommendations) < 6:
            remaining_questions = Question.query.filter_by(
                is_public=True,
                difficulty=user_profile['preferred_difficulty']
            ).limit(6 - len(recommendations)).all()
            
            for question in remaining_questions:
                if not any(r['id'] == question.id for r in recommendations):
                    recommendation = create_recommendation(question, user_profile, 'general')
                    recommendations.append(recommendation)
        
        return recommendations[:6]  # 最大6問まで
        
    except Exception as e:
        logger.error(f'Failed to get recommended questions: {str(e)}')
        return []

# 推奨情報の作成
def create_recommendation(question, user_profile, reason_type):
    """推奨問題の情報を作成"""
    # 推奨度スコアを計算
    recommendation_score = calculate_recommendation_score(question, user_profile, reason_type)
    
    # 推奨理由を生成
    reason_messages = {
        'weakness_improvement': f'{get_category_text(question.category)}分野の強化',
        'skill_advancement': f'{get_category_text(question.category)}分野のレベルアップ',
        'exploration': f'{get_category_text(question.category)}分野の新規挑戦',
        'general': '学習進捗に最適'
    }
    
    recommendation_reason = reason_messages.get(reason_type, '学習進捗に最適')
    
    return {
        'id': question.id,
        'question_text': question.question_text,
        'difficulty': question.difficulty,
        'category': question.category,
        'play_count': question.play_count or 0,
        'avg_score': question.avg_score or 0,
        'recommendation_score': recommendation_score,
        'recommendation_reason': recommendation_reason,
        'confidence': min(0.9, 0.5 + (recommendation_score / 100) * 0.4)
    }

# 推奨度スコアの計算
def calculate_recommendation_score(question, user_profile, reason_type):
    """推奨度スコアを計算（0-100）"""
    base_score = 50
    
    # 理由に基づくボーナス
    reason_bonus = {
        'weakness_improvement': 30,
        'skill_advancement': 25,
        'exploration': 20,
        'general': 10
    }
    base_score += reason_bonus.get(reason_type, 0)
    
    # 難易度の適合性
    if question.difficulty == user_profile['preferred_difficulty']:
        base_score += 15
    elif question.difficulty == get_next_difficulty(user_profile['preferred_difficulty']):
        base_score += 10
    
    # 分野の適合性
    if question.category in user_profile['weaknesses']:
        base_score += 20
    elif question.category in user_profile['strengths']:
        base_score += 15
    elif question.category not in user_profile['preferred_categories']:
        base_score += 10
    
    return min(100, max(0, base_score))

# 次の難易度を取得
def get_next_difficulty(current_difficulty):
    """現在の難易度の次のレベルを取得"""
    difficulty_order = ['easy', 'medium', 'hard']
    try:
        current_index = difficulty_order.index(current_difficulty)
        if current_index < len(difficulty_order) - 1:
            return difficulty_order[current_index + 1]
        return current_difficulty
    except ValueError:
        return 'medium'

# カテゴリテキストの取得
def get_category_text(category):
    """カテゴリの日本語テキストを取得"""
    category_texts = {
        'conversation': '会話',
        'news': 'ニュース',
        'story': '物語',
        'academic': '学術'
    }
    return category_texts.get(category, category)

# 連続学習日数の計算
def calculate_learning_streak(logs):
    """連続学習日数を計算"""
    if not logs:
        return 0
    
    # 日付順にソート
    sorted_logs = sorted(logs, key=lambda x: x.created_at)
    
    streak = 1
    current_date = sorted_logs[-1].created_at.date()
    
    for i in range(len(sorted_logs) - 2, -1, -1):
        log_date = sorted_logs[i].created_at.date()
        days_diff = (current_date - log_date).days
        
        if days_diff == 1:
            streak += 1
            current_date = log_date
        elif days_diff > 1:
            break
    
    return streak

# コンテンツの推薦（既存のAPI、互換性のため残す）
@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    logs = LearningLog.query.filter_by(user_id=user_id).all()
    learning_data = [{'question_id': log.question_id, 'score': (log.score or 0)} for log in logs]
    recommendations = recommend_content(learning_data)
    return jsonify({'recommendations': recommendations}), 200


# ユーザーの進捗・スコア履歴を取得
@app.route('/user_progress', methods=['GET'])
def user_progress():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    logs = LearningLog.query.filter_by(user_id=user_id).order_by(LearningLog.id.desc()).all()
    results = [
        {
            'id': log.id,
            'user_id': log.user_id,
            'question_id': log.question_id,
            'content_id': log.content_id,
            'user_answer': log.user_answer,
            'score': log.score,
        }
        for log in logs
    ]
    return jsonify({'logs': results}), 200

# 復習機能のルート
@app.route('/review')
@login_required
def review():
    """復習ページを表示"""
    return render_template('review.html')

# 間違えた問題の取得
@app.route('/api/review/wrong-questions')
@login_required
def get_wrong_questions():
    """ユーザーが間違えた問題のリストを取得"""
    try:
        # LearningLogから間違えた問題を取得
        wrong_logs = LearningLog.query.filter_by(
            user_id=current_user.id,
            completion_status=True
        ).filter(
            LearningLog.score < 100  # 100点未満を間違いとみなす
        ).order_by(LearningLog.id.desc()).all()
        
        # 問題IDごとにグループ化して間違えた回数をカウント
        wrong_questions = {}
        for log in wrong_logs:
            if log.question_id:
                if log.question_id not in wrong_questions:
                    question = Question.query.get(log.question_id)
                    if question:
                        wrong_questions[log.question_id] = {
                            'id': question.id,
                            'question_text': question.question_text,
                            'correct_answer': question.correct_answer,
                            'audio_url': question.audio_url,
                            'wrong_count': 1,
                            'wrong_date': log.created_at.isoformat() if log.created_at else None,
                            'last_score': log.score
                        }
                else:
                    wrong_questions[log.question_id]['wrong_count'] += 1
                    if log.score < wrong_questions[log.question_id]['last_score']:
                        wrong_questions[log.question_id]['last_score'] = log.score
        
        return jsonify(list(wrong_questions.values()))
    except Exception as e:
        logger.error(f"間違えた問題の取得エラー: {e}")
        return jsonify({'error': '間違えた問題の取得に失敗しました'}), 500

# 学習履歴の取得（復習用）
@app.route('/api/review/learning-history')
@login_required
def get_review_learning_history():
    """ユーザーの学習履歴を取得（復習用）"""
    try:
        logs = LearningLog.query.filter_by(
            user_id=current_user.id
        ).order_by(LearningLog.id.desc()).limit(20).all()
        
        history = []
        for log in logs:
            if log.question_id:
                question = Question.query.get(log.question_id)
                history.append({
                    'id': log.id,
                    'content_title': question.question_text if question else '問題',
                    'study_date': log.created_at.isoformat() if log.created_at else None,
                    'score': log.score,
                    'time_spent': log.time_spent,
                    'completion_status': log.completion_status
                })
        
        return jsonify(history)
    except Exception as e:
        logger.error(f"学習履歴の取得エラー: {e}")
        return jsonify({'error': '学習履歴の取得に失敗しました'}), 500

# 回答履歴の取得
@app.route('/api/review/answer-history')
@login_required
def get_answer_history():
    """ユーザーの回答履歴を取得"""
    try:
        logs = LearningLog.query.filter_by(
            user_id=current_user.id,
            completion_status=True
        ).filter(
            LearningLog.user_answer.isnot(None)
        ).order_by(LearningLog.id.desc()).limit(20).all()
        
        history = []
        for log in logs:
            if log.question_id:
                question = Question.query.get(log.question_id)
                if question:
                    history.append({
                        'id': log.id,
                        'question_text': question.question_text,
                        'user_answer': log.user_answer,
                        'correct_answer': question.correct_answer,
                        'is_correct': log.user_answer == question.correct_answer,
                        'answer_date': log.created_at.isoformat() if log.created_at else None,
                        'score': log.score
                    })
        
        return jsonify(history)
    except Exception as e:
        logger.error(f"回答履歴の取得エラー: {e}")
        return jsonify({'error': '回答履歴の取得に失敗しました'}), 500

# 特定の問題の詳細取得
@app.route('/api/review/question/<int:question_id>')
@login_required
def get_question_for_review(question_id):
    """復習用の問題詳細を取得"""
    try:
        question = Question.query.get_or_404(question_id)
        return jsonify({
            'id': question.id,
            'question_text': question.question_text,
            'correct_answer': question.correct_answer,
            'audio_url': question.audio_url,
            'option_a': '選択肢A',  # 実際の実装では選択肢も保存する必要がある
            'option_b': '選択肢B',
            'option_c': '選択肢C',
            'option_d': '選択肢D'
        })
    except Exception as e:
        logger.error(f"問題詳細の取得エラー: {e}")
        return jsonify({'error': '問題詳細の取得に失敗しました'}), 500

# 復習開始
@app.route('/api/review/start', methods=['POST'])
@login_required
def start_review():
    """復習を開始"""
    try:
        data = request.json
        question_id = data.get('question_id')
        
        if not question_id:
            return jsonify({'error': '問題IDが必要です'}), 400
        
        # 復習ログを作成
        review_log = LearningLog(
            user_id=current_user.id,
            content_id=question_id,
            question_id=question_id,
            completion_status=False,
            time_spent=0.0
        )
        db.session.add(review_log)
        db.session.commit()
        
        return jsonify({'success': True, 'review_id': review_log.id})
    except Exception as e:
        logger.error(f"復習開始エラー: {e}")
        return jsonify({'error': '復習開始に失敗しました'}), 500

# ユーザープロフィール取得（復習機能用）
@app.route('/api/user/profile')
@login_required
def get_user_profile():
    """ユーザープロフィールを取得"""
    try:
        return jsonify({
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email
        })
    except Exception as e:
        logger.error(f"ユーザープロフィール取得エラー: {e}")
        return jsonify({'error': 'ユーザープロフィールの取得に失敗しました'}), 500

# 復習結果の保存
@app.route('/api/review/save-result', methods=['POST'])
@login_required
def save_review_result():
    """復習結果を保存"""
    try:
        data = request.json
        question_id = data.get('question_id')
        user_answer = data.get('user_answer')
        is_correct = data.get('is_correct')
        time_spent = data.get('time_spent', 0)
        
        if not question_id or user_answer is None:
            return jsonify({'error': '必要なデータが不足しています'}), 400
        
        # 復習ログを作成または更新
        review_log = LearningLog(
            user_id=current_user.id,
            content_id=question_id,
            question_id=question_id,
            user_answer=user_answer,
            score=100 if is_correct else 0,
            completion_status=True,
            time_spent=time_spent,
            is_review=True,
            review_count=1
        )
        
        db.session.add(review_log)
        db.session.commit()
        
        return jsonify({'success': True, 'review_id': review_log.id})
    except Exception as e:
        logger.error(f"復習結果保存エラー: {e}")
        return jsonify({'error': '復習結果の保存に失敗しました'}), 500

# 復習詳細ページの表示
@app.route('/review/<int:question_id>')
@login_required
def review_detail(question_id):
    """復習詳細ページを表示"""
    try:
        question = Question.query.get_or_404(question_id)
        
        # 間違えた回数と前回のスコアを取得
        wrong_logs = LearningLog.query.filter_by(
            user_id=current_user.id,
            question_id=question_id
        ).filter(
            LearningLog.score < 100
        ).order_by(LearningLog.id.desc()).all()
        
        wrong_count = len(wrong_logs)
        last_score = wrong_logs[0].score if wrong_logs else 0
        
        # 復習回数を取得
        review_logs = LearningLog.query.filter_by(
            user_id=current_user.id,
            question_id=question_id,
            is_review=True
        ).all()
        review_count = len(review_logs)
        
        return render_template('review_detail.html', 
                            question=question,
                            wrong_count=wrong_count,
                            last_score=last_score,
                            review_count=review_count)
    except Exception as e:
        logger.error(f"復習詳細ページ表示エラー: {e}")
        flash('復習ページの表示に失敗しました', 'error')
        return redirect(url_for('review'))

if __name__ == '__main__':
    # instanceディレクトリが存在しない場合は作成
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    
    with app.app_context():
        try:
            # データベースファイルが存在しない場合のみテーブルを作成
            if not os.path.exists(db_path):
                db.create_all()
                print("データベースとテーブルを作成しました")
                
                # 初回起動時のみサンプルユーザーを作成
                from werkzeug.security import generate_password_hash
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    password=generate_password_hash('password123')
                )
                db.session.add(admin_user)
                db.session.commit()
                print("サンプルユーザー（admin/password123）を作成しました")
            else:
                print("既存のデータベースを使用します")
        except Exception as e:
            print(f"データベース初期化エラー: {e}")
            print("アプリは起動しますが、データベース機能は利用できません")
    
    app.run(debug=True)
