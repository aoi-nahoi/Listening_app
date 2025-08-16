#!/usr/bin/env python3
"""
復習機能のテスト用サンプルデータを作成するスクリプト
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import app, db
from models import User, Question, LearningLog, TestResult
from werkzeug.security import generate_password_hash

def create_sample_data():
    """サンプルデータを作成する"""
    with app.app_context():
        try:
            # 既存のデータを確認
            user_count = User.query.count()
            question_count = Question.query.count()
            log_count = LearningLog.query.count()
            
            print(f"現在のデータ状況:")
            print(f"- ユーザー数: {user_count}")
            print(f"- 問題数: {question_count}")
            print(f"- 学習ログ数: {log_count}")
            
            # サンプル問題を作成
            if question_count == 0:
                print("\nサンプル問題を作成中...")
                
                # サンプル問題のデータ
                sample_questions = [
                    {
                        'audio_url': '/static/audio/sample1.mp3',
                        'question_text': 'What did you do yesterday?',
                        'correct_answer': 'I went to the park.',
                        'option_a': 'I went to the park.',
                        'option_b': 'I will go to the park.',
                        'option_c': 'I am going to the park.',
                        'option_d': 'I have been to the park.',
                        'difficulty_level': 1
                    },
                    {
                        'audio_url': '/static/audio/sample2.mp3',
                        'question_text': 'How long have you been studying English?',
                        'correct_answer': 'For three years.',
                        'option_a': 'Since three years.',
                        'option_b': 'For three years.',
                        'option_c': 'Three years ago.',
                        'option_d': 'In three years.',
                        'difficulty_level': 2
                    },
                    {
                        'audio_url': '/static/audio/sample3.mp3',
                        'question_text': 'Could you help me with this?',
                        'correct_answer': 'Of course, I\'d be happy to help.',
                        'option_a': 'Of course, I\'d be happy to help.',
                        'option_b': 'I don\'t know.',
                        'option_c': 'Maybe later.',
                        'option_d': 'That\'s not my problem.',
                        'difficulty_level': 1
                    }
                ]
                
                # ユーザーを取得（最初のユーザーを使用）
                user = User.query.first()
                if not user:
                    print("ユーザーが存在しません。先にユーザーを作成してください。")
                    return False
                
                for i, q_data in enumerate(sample_questions):
                    question = Question(
                        audio_url=q_data['audio_url'],
                        question_text=q_data['question_text'],
                        correct_answer=q_data['correct_answer'],
                        option_a=q_data['option_a'],
                        option_b=q_data['option_b'],
                        option_c=q_data['option_c'],
                        option_d=q_data['option_d'],
                        uploaded_by=user.id,
                        is_public=True,
                        difficulty_level=q_data['difficulty_level']
                    )
                    db.session.add(question)
                
                db.session.commit()
                print(f"{len(sample_questions)}個のサンプル問題を作成しました")
            
            # サンプル学習ログを作成
            if log_count == 0:
                print("\nサンプル学習ログを作成中...")
                
                # 問題を取得
                questions = Question.query.all()
                if not questions:
                    print("問題が存在しません。先に問題を作成してください。")
                    return False
                
                user = User.query.first()
                
                # 過去7日間の学習ログを作成
                for i in range(7):
                    date = datetime.now() - timedelta(days=i)
                    
                    # 各日に2-4個の学習ログを作成
                    for j in range(random.randint(2, 4)):
                        question = random.choice(questions)
                        score = random.randint(60, 95)  # 60-95点（間違えた問題として扱う）
                        
                        log = LearningLog(
                            user_id=user.id,
                            content_id=question.id,
                            question_id=question.id,
                            user_answer=random.choice([question.option_a, question.option_b, question.option_c, question.option_d]),
                            score=score,
                            time_spent=random.uniform(2.0, 8.0),
                            completion_status=True,
                            review_count=random.randint(0, 3),
                            is_review=random.choice([True, False])
                        )
                        db.session.add(log)
                
                db.session.commit()
                print("サンプル学習ログを作成しました")
            
            print("\nサンプルデータの作成が完了しました！")
            print("復習ページでテストできるようになりました。")
            
            return True
            
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            return False

if __name__ == '__main__':
    create_sample_data()
