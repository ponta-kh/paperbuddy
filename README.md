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
├── docs/             # アーキテクチャ・設計ドキュメント
├── docker/           # Docker関連
├── frontend/         # React アプリケーション
└── infra/            # AWSインフラ定義
```

## ローカル開発

ローカル起動は、AWS ECS Fargateでのデプロイ状況へ極力揃えるためDocker Compose経由を標準とする。
バックエンドをホスト上の`uvicorn`で直接起動する方法は禁止する。

初回のみ、ローカル用の環境変数ファイルを作成して値を設定する。

```sh
cp docker/.env.example docker/.env
```

フロントエンドとバックエンドは、リポジトリルートから次のコマンドでDocker経由で同時に起動する。

```sh
mise run dev
```

- フロントエンド: `http://localhost:5173`
- バックエンドヘルスチェック: `http://localhost:8000/api/health`
- フロントエンドからの `/api/*` リクエストは、Viteがバックエンドへプロキシする
- CognitoはAWS上のローカル開発用User PoolとWeb App Clientを使用する

フロントエンド改修を即時反映したい場合は、バックエンドだけをDocker経由で起動し、
フロントエンドをホスト上の`pnpm dev`で起動する。

```sh
mise run dev:backend
mise run dev:frontend
```

ローカルバックエンドはDynamoDB Localを使用する。Repository実装はAWS上のDynamoDB接続時と同じものを使い、
エンドポイントだけをDocker Composeの環境変数で切り替える。
