# PaperBuddy Backend

## Prerequisites

- Python 3.14 and uv
- An AWS profile with access to the target Bedrock Knowledge Base and model
- Model access enabled in the AWS region used by the Knowledge Base

The application uses boto3's standard AWS credential provider chain. Do not put
AWS access keys in `.env`.

アプリケーション固有の環境変数は
`src/dependencies/settings.py`のPydantic Settingsへ集約している。

- 共通必須: `AWS_REGION`、`DYNAMODB_CHAT_TABLE_NAME`
- AWSモード必須: `BEDROCK_KNOWLEDGE_BASE_ID`、`BEDROCK_MODEL_ARN`
- ローカルモード必須: `DYNAMODB_ENDPOINT_URL`
- 任意: `CHAT_INFRASTRUCTURE_MODE`、`SIMULATED_LLM_DELAY_SECONDS`
- Boto3認証用: `AWS_PROFILE`などの標準AWS環境変数

## Local Configuration

Create the local environment file and replace the Bedrock identifiers:

```sh
cp .env.example .env
```

For an AWS SSO profile, authenticate before starting the backend:

```sh
aws sso login --profile your-profile
AWS_PROFILE=your-profile aws sts get-caller-identity
```

Set the same profile name in `.env`.

The local and deployed backends both use the persistent DynamoDB repository.
Deploy the development table and set:

```dotenv
DYNAMODB_CHAT_TABLE_NAME=paperbuddy-dev-chat
```

See `docs/infra/dynamodb.md` for deployment, authentication, and IAM
requirements. The table and `gsi1` key schema are defined in
`docs/backend/specification/integrations/dynamodb_chat_repository.md`.

## Run on the Host

```sh
uv sync
uv run uvicorn main:app --reload --env-file .env
```

## Run with Docker Compose

The Compose service mounts the host's `~/.aws` directory read-only so boto3 can
use the configured profile and AWS SSO cache. It overrides the container user
to root locally so AWS files with `0600` permissions remain readable. The
production Docker image still runs as a non-root user.

```sh
docker compose up --build
```

## ローカル全体動作確認

実AWSへ接続せずに画面から一連のチャット操作を確認する場合は、リポジトリルートで
以下を実行する。

```sh
mise run dev:local
```

- バックエンド: `http://localhost:8000`
- フロントエンド: `http://localhost:5173`
- DB: DynamoDB Localコンテナ。データはDocker Volumeへ保存する
- LLM: 既定で2秒待機し、300文字の疑似回答を返す
- 初期データ: 今日2件、過去7日間3件、1週間以上前6件の会話履歴

`CHAT_INFRASTRUCTURE_MODE=local`の場合だけローカル用Infrastructureを注入する。
通常起動およびAWSデプロイでは、既存のDynamoDB・Bedrock実装を使用する。

バックエンドとDynamoDB Localを停止する場合は以下を実行する。

```sh
docker compose -f backend/compose.local.yaml down
```

DynamoDB Localの保存データも初期化する場合は、`--volumes`を追加する。

## Test the Bedrock Connection

Start the backend, then create a chat. This calls both Knowledge Base
`RetrieveAndGenerate` and Bedrock Runtime `Converse`.

```sh
curl --fail-with-body \
  -X POST http://localhost:8000/api/chats \
  -H 'Content-Type: application/json' \
  -H 'X-User-ID: 00000000-0000-0000-0000-000000000001' \
  -d '{"prompt":"このナレッジベースの内容を簡潔に説明してください"}'
```

Required permissions for the AWS identity include:

- `bedrock:RetrieveAndGenerate`
- `bedrock:InvokeModel`

The Bedrock Knowledge Base and model must be available in `AWS_REGION`.

## Automated Tests

Run the backend test suite with the domain and use-case coverage gates:

```sh
mise run backend:test
```

- `backend:test:domain` enforces 100% statement and branch coverage for executable Domain code.
- `backend:test:application` tests use cases with output-port mocks and enforces 100% statement and branch coverage.
- Repository Protocol declarations are excluded from runtime coverage because they contain no executable domain behavior.
