# 英語リスニング学習アプリ

## 概要

英語リスニング学習アプリは、音声ファイルをアップロードして自動的に穴埋め問題を生成し、ユーザーの英語リスニング能力向上を支援するWebアプリケーションです。Google Cloud Speech-to-Text APIを使用した音声認識機能と、機械学習による推奨システムを備えています。

## 主な機能

### 🔐 ユーザー認証・管理
- ユーザー登録・ログイン・ログアウト
- プロフィール管理
- 学習進捗の追跡

### 🎵 音声学習
- 音声ファイルのアップロード（MP3、WAV等）
- Google Cloud Speech-to-Text APIによる自動音声認識
- 音声から自動生成される穴埋め問題
- 音声再生機能

### 📚 学習システム
- 問題一覧表示
- 問題学習ページ
- 回答提出と自動採点
- 学習ログの記録
- 正答率・スコアの追跡

### 🔄 復習機能
- 間違えた問題の自動抽出
- 復習センター
- 学習履歴の表示
- スコア推移グラフ
- 復習回数の追跡

### 🤖 推奨システム
- ユーザーの学習履歴に基づく個別推奨
- 得意・不得意分野の分析
- 適切な難易度の問題推奨
- 新しい分野の探索推奨

### 📊 ダッシュボード
- 学習進捗の可視化
- 最近の問題表示
- 統計情報の表示

## 技術スタック

### バックエンド
- **Python 3.x**
- **Flask**: Webフレームワーク
- **SQLAlchemy**: ORM
- **Flask-Migrate**: データベースマイグレーション
- **Flask-Login**: ユーザー認証管理
- **Werkzeug**: ファイルアップロード処理

### データベース
- **SQLite**: 開発用データベース
- **PostgreSQL**: 本番環境用データベース（Render対応）
- **Alembic**: データベースマイグレーション管理

### 外部API
- **Google Cloud Speech-to-Text API**: 音声認識

### フロントエンド
- **HTML5**: マークアップ
- **CSS3**: スタイリング
- **JavaScript**: インタラクティブ機能
- **Bootstrap 5**: UIフレームワーク
- **Chart.js**: グラフ表示

### 開発・運用
- **Flask-Migrate**: データベーススキーマ管理
- **Logging**: ログ管理

## プロジェクト構造

```
listening_app/
├── app.py                          # メインアプリケーションファイル
├── models.py                       # データベースモデル定義
├── extensions.py                   # Flask拡張機能の初期化
├── ml_recommendations.py          # 機械学習推奨システム
├── logging_config.py              # ログ設定
├── create_db.py                   # データベース初期化スクリプト
├── create_sample_data.py          # サンプルデータ作成スクリプト
├── requirements.txt               # Python依存関係
├── README.md                      # プロジェクト説明書
├── REVIEW_FEATURE_README.md       # 復習機能詳細説明
│
├── instance/                      # インスタンス固有ファイル
│   └── listening.db              # SQLiteデータベース
│
├── migrations/                    # データベースマイグレーション
│   ├── alembic.ini              # Alembic設定
│   ├── env.py                   # マイグレーション環境
│   ├── script.py.mako           # マイグレーションスクリプトテンプレート
│   └── versions/                # マイグレーションバージョン
│       ├── 69fd92cec8e7_initial_migration.py
│       ├── add_review_fields.py
│       └── c10d2c06536c_add_uploaded_by_and_is_public_to_.py
│
├── static/                       # 静的ファイル
│   ├── audio/                   # アップロードされた音声ファイル
│   ├── css/                     # スタイルシート
│   │   ├── style.css           # メインスタイル
│   │   └── review.css          # 復習機能用スタイル
│   └── js/                     # JavaScriptファイル
│       ├── main.js             # メインJavaScript
│       └── review.js           # 復習機能用JavaScript
│
└── templates/                    # HTMLテンプレート
    ├── base.html                # ベーステンプレート
    ├── login.html               # ログインページ
    ├── register.html            # ユーザー登録ページ
    ├── dashboard.html           # ダッシュボード
    ├── profile.html             # ユーザープロフィール
    ├── questions.html           # 問題一覧
    ├── learn.html               # 学習ページ
    ├── upload.html              # 音声アップロード
    ├── review.html              # 復習センター
    ├── review_detail.html       # 復習詳細ページ
    └── recommendations.html     # 推奨コンテンツ
```

## データベースモデル

### User
- ユーザー情報（ID、ユーザー名、メール、パスワード）
- アップロードした問題との関連

### Question
- 問題情報（音声URL、問題文、正解、選択肢）
- 難易度レベル、カテゴリ、公開設定
- アップローダー情報

### LearningLog
- 学習記録（ユーザーID、問題ID、スコア、回答）
- 学習時間、完了状況、復習回数

### TestResult
- テスト結果（ユーザーID、テストID、スコア、間違い内容）

## セットアップ手順

### 1. 環境要件
- Python 3.7以上
- pip（Pythonパッケージマネージャー）
- Google Cloud Platform アカウント（音声認識API用）

### 2. リポジトリのクローン
```bash
git clone <repository-url>
cd listening_app
```

### 3. 仮想環境の作成とアクティベート
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 5. Google Cloud Speech-to-Text APIの設定
```bash
# Google Cloud CLIのインストール
# https://cloud.google.com/sdk/docs/install

# 認証情報の設定
gcloud auth application-default login

# プロジェクトの設定
gcloud config set project YOUR_PROJECT_ID
```

### 6. 環境変数の設定
```bash
# 開発環境用の環境変数設定
# .envファイルを作成して以下の内容を設定

# データベース設定（開発環境ではSQLiteを使用）
# DATABASE_URL=sqlite:///instance/listening.db

# 本番環境ではPostgreSQLを使用
# DATABASE_URL=postgresql://username:password@localhost:5432/listening_app

# セキュリティ設定
SECRET_KEY=your-secret-key-here

# Google Cloud Speech-to-Text API設定
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json

# Windows
set GOOGLE_APPLICATION_CREDENTIALS=path\to\your\credentials.json

# macOS/Linux
export GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
```

### 7. データベースの初期化
```bash
# データベースとテーブルの作成
python create_db.py

# マイグレーションの実行
flask db upgrade
```

### 8. サンプルデータの作成（オプション）
```bash
python create_sample_data.py
```

## 起動コマンド

### 開発サーバーの起動
```bash
python app.py
```

### 本番環境での起動
```bash
# Gunicornを使用（推奨）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# または
flask run --host=0.0.0.0 --port=5000
```

### データベースマイグレーション
```bash
# 新しいマイグレーションの作成
flask db migrate -m "Description of changes"

# マイグレーションの適用
flask db upgrade

# マイグレーションの履歴確認
flask db history
```

## 使用方法

### 1. 初回アクセス
- アプリケーションにアクセス
- ユーザー登録を実行
- ログイン

### 2. 音声ファイルのアップロード
- アップロードページに移動
- 音声ファイルを選択
- 公開設定を選択
- アップロード実行

### 3. 学習の開始
- 問題一覧から学習したい問題を選択
- 音声を聞いて問題を理解
- 回答を入力
- 結果を確認

### 4. 復習の実行
- 復習センターにアクセス
- 間違えた問題を確認
- 復習を開始
- 学習効果を測定

## API エンドポイント

### 認証
- `POST /login`: ユーザーログイン
- `POST /register`: ユーザー登録
- `GET /logout`: ログアウト

### 学習
- `GET /questions`: 問題一覧
- `GET /learn/<id>`: 問題学習
- `POST /api/submit_answer`: 回答提出
- `GET /api/questions/public`: 公開問題取得

### 音声アップロード
- `GET /upload`: アップロードページ
- `POST /upload_audio`: 音声ファイルアップロード

### 復習機能
- `GET /review`: 復習センター
- `GET /api/review/wrong-questions`: 間違えた問題取得
- `POST /api/review/save-result`: 復習結果保存

### 推奨システム
- `GET /recommendations`: 推奨コンテンツ
- `GET /api/recommendations`: 推奨API

## 設定

### アプリケーション設定
- `SECRET_KEY`: セッション暗号化キー
- `SQLALCHEMY_DATABASE_URI`: データベース接続URI
- `UPLOAD_FOLDER`: 音声ファイル保存先
- `GOOGLE_APPLICATION_CREDENTIALS`: Google Cloud認証情報

### データベース設定
- SQLite（開発用）
- PostgreSQL/MySQL（本番用推奨）

## 開発ガイド

### コード規約
- Python: PEP 8準拠
- HTML: HTML5準拠
- CSS: BEM命名規則推奨
- JavaScript: ES6+準拠

### テスト
```bash
# テストの実行
python -m pytest tests/

# カバレッジの確認
python -m pytest --cov=app tests/
```

### デバッグ
- Flask debug mode有効
- ログレベルの調整
- データベースクエリの確認

## デプロイ

### Renderでのデプロイ

1. **GitHubリポジトリの準備**
   - コードをGitHubリポジトリにプッシュ

2. **Renderでの設定**
   - Render.comにアクセスしてアカウント作成
   - "New +" → "Web Service"を選択
   - GitHubリポジトリを接続
   - 以下の設定を行う：
     - **Build Command**: `pip install -r requirements.txt && flask db upgrade`
     - **Start Command**: `gunicorn app:app`
     - **Environment Variables**:
       - `SECRET_KEY`: ランダムな文字列を生成
       - `DATABASE_URL`: RenderのPostgreSQLデータベースの接続文字列（自動設定）
       - `GOOGLE_APPLICATION_CREDENTIALS`: Google Cloud認証情報（手動設定）

3. **PostgreSQLデータベースの作成**
   - Renderダッシュボードで"New +" → "PostgreSQL"を選択
   - データベース名を設定（例：listening-db）
   - 接続文字列が自動的に`DATABASE_URL`環境変数に設定される

4. **デプロイの実行**
   - 設定完了後、自動的にデプロイが開始される
   - デプロイ完了後、提供されたURLでアプリケーションにアクセス可能

### 本番環境での注意点
1. `SECRET_KEY`を環境変数から取得
2. データベースをPostgreSQLに変更（完了）
3. 静的ファイルのCDN配信
4. HTTPS通信の有効化
5. ログローテーションの設定

### Docker化
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## トラブルシューティング

### よくある問題

1. **音声認識が動作しない**
   - Google Cloud API認証情報を確認
   - 音声ファイル形式を確認（16kHz, LINEAR16推奨）

2. **データベースエラー**
   - マイグレーションの実行状況を確認
   - データベースファイルの権限を確認

3. **ファイルアップロードエラー**
   - アップロードディレクトリの権限を確認
   - ファイルサイズ制限を確認

### ログの確認
```bash
# アプリケーションログ
tail -f app.log

# データベースログ
tail -f database.log
```

## 今後の拡張予定

### 短期（1-3ヶ月）
- [ ] 音声品質の向上
- [ ] 問題生成アルゴリズムの改善
- [ ] モバイル対応の強化

### 中期（3-6ヶ月）
- [ ] 機械学習モデルの導入
- [ ] 音声合成機能の追加
- [ ] 多言語対応

### 長期（6ヶ月以上）
- [ ] AI講師機能
- [ ] 学習コミュニティ機能
- [ ] VR/AR学習環境

## 貢献

### 開発への参加
1. このリポジトリをフォーク
2. 機能ブランチを作成
3. 変更をコミット
4. プルリクエストを作成

### 報告事項
- バグ報告
- 機能要望
- ドキュメント改善提案

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## サポート

### ドキュメント
- [API仕様書](docs/api.md)
- [データベース設計書](docs/database.md)
- [デプロイガイド](docs/deploy.md)

### コミュニティ
- [Issues](https://github.com/your-repo/issues)
- [Discussions](https://github.com/your-repo/discussions)

### 連絡先
- プロジェクトメンテナー: [your-email@example.com]
- プロジェクトURL: [https://github.com/your-repo]

---

**注意**: 本アプリケーションを使用する前に、Google Cloud Speech-to-Text APIの利用規約と料金体系を確認してください。
