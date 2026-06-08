# PaperBuddy
AI論文リサーチャー
RAGによってアップロード済みの論文群を横断的に検索・要約し、チャット形式で対話できるWebアプリケーション

## 技術スタック
| レイヤー | 技術 |
|---|---|
| フロントエンド | React / TypeScript |
| バックエンド | FastAPI / Python |
| LLM | AWS Bedrock (Claude) |
| RAG | Amazon Bedrock Knowledge Bases + S3 |
| 認証 | Amazon Cognito |
| インフラ | ECS on Fargate / ALB / CloudFront / VPC Origins |
| パッケージ管理 | uv (Python) / pnpm (Node) |
 
## ディレクトリ構成
```
paperbuddy/
├── backend/          # FastAPI アプリケーション
├── frontend/         # React アプリケーション
├── infra/            # AWSインフラ定義
└── docs/             # アーキテクチャ・設計ドキュメント
```

## ローカル開発

初回のみ、ローカル用の環境変数ファイルを作成して値を設定する。

```sh
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

フロントエンドとバックエンドは、リポジトリルートから次のコマンドで同時に起動する。

```sh
mise run dev
```

- フロントエンド: `http://localhost:5173`
- バックエンドヘルスチェック: `http://localhost:8000/api/health`
- フロントエンドからの `/api/*` リクエストは、Viteがバックエンドへプロキシする
