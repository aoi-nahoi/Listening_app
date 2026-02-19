from extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    # 登録日: マイグレーション add_user_created_at 適用後にカラムを追加し、ここに created_at を定義するとプロフィールで表示されます
    questions = db.relationship('Question', backref='uploader', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    audio_url = db.Column(db.String(255), nullable=False)  # 音声ファイルのURL
    question_text = db.Column(db.String(255), nullable=False)  # 質問文
    correct_answer = db.Column(db.String(255), nullable=False)  # 正解
    option_a = db.Column(db.String(255), nullable=True)  # 選択肢A
    option_b = db.Column(db.String(255), nullable=True)  # 選択肢B
    option_c = db.Column(db.String(255), nullable=True)  # 選択肢C
    option_d = db.Column(db.String(255), nullable=True)  # 選択肢D
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #誰がアップロードしたか
    is_public = db.Column(db.Boolean, default=True) #デフォルトで公開
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  # 作成日時
    difficulty_level = db.Column(db.Integer, nullable=True, default=1)  # 難易度レベル（1-5）

    @property
    def difficulty(self):
        """難易度レベル(1-5)を easy/medium/hard に変換（API・テンプレート互換）"""
        level = self.difficulty_level or 1
        if level <= 2:
            return 'easy'
        if level <= 3:
            return 'medium'
        return 'hard'

    @property
    def category(self):
        """カテゴリ（未実装の場合は None。API・テンプレート互換）"""
        return None

    @property
    def play_count(self):
        """再生回数（未実装の場合は 0）"""
        return 0

    @property
    def avg_score(self):
        """平均スコア（未実装の場合は 0）"""
        return 0

    def __repr__(self):
        return f'<Question {self.id}: {self.question_text}>'

class LearningLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # ユーザーID
    content_id = db.Column(db.Integer, nullable=False)  # コンテンツID
    time_spent = db.Column(db.Float, nullable=False, default=0.0)  # 学習時間 (分単位)
    completion_status = db.Column(db.Boolean, nullable=False, default=False)  # 学習完了状況 (True/False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=True)  # Optional
    user_answer = db.Column(db.String(255), nullable=True)  # Optional
    score = db.Column(db.Integer, nullable=True)  # Optional
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  # 作成日時
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())  # 更新日時
    review_count = db.Column(db.Integer, nullable=False, default=0)  # 復習回数
    is_review = db.Column(db.Boolean, nullable=False, default=False)  # 復習かどうか

    def __repr__(self):
        return f'<LearningLog User {self.user_id}, Content {self.content_id}, Status {self.completion_status}>'

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # ユーザーID
    test_id = db.Column(db.Integer, nullable=False)  # テストID
    score = db.Column(db.Integer, nullable=False)  # 得点
    mistakes = db.Column(db.String(255))  # 間違えた内容や種類

    def __repr__(self):
        return f'<TestResult User: {self.user_id}, Score: {self.score}>'
