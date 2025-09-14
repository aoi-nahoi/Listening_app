#!/usr/bin/env python3
"""
データベースを再作成するスクリプト
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import app, db
from models import User, Question, LearningLog, TestResult

def create_database():
    """データベースとテーブルを作成する"""
    with app.app_context():
        try:
            # SQLiteの場合のみ既存ファイルを削除
            if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
                db_path = Path('instance/listening.db')
                if db_path.exists():
                    db_path.unlink()
                    print("既存のデータベースファイルを削除しました")
            
            # データベースとテーブルを作成
            db.create_all()
            print("データベースとテーブルを作成しました")
            
            # サンプルユーザーを作成
            from werkzeug.security import generate_password_hash
            
            # ユーザーが存在しない場合のみ作成
            if not User.query.filter_by(username='admin').first():
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    password=generate_password_hash('password123')
                )
                db.session.add(admin_user)
                db.session.commit()
                print("サンプルユーザー（admin/password123）を作成しました")
            
            print("データベースの初期化が完了しました！")
            
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            return False
    
    return True

if __name__ == '__main__':
    create_database()
