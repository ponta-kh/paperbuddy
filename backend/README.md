# PaperBuddy Backend

## Prerequisites

- Python 3.14 and uv
- AWS CLIで対象アカウントへログイン済みであること
- Model access enabled in the AWS region used by the Knowledge Base

The application uses boto3's standard AWS credential provider chain. Do not put
AWS access keys in `.env`.

アプリケーション固有の環境変数は
`src/dependencies/settings.py`のPydantic Settingsへ集約している。

- 共通必須: `AWS_REGION`、`DYNAMODB_CHAT_TABLE_NAME`、`DYNAMODB_LIBRARY_TABLE_NAME`
- 認証必須: `COGNITO_USER_POOL_ID`、`COGNITO_USER_POOL_CLIENT_ID`
- AWSモード必須: `BEDROCK_KNOWLEDGE_BASE_ID`、`BEDROCK_MODEL_ARN`
- ローカルモード必須: `DYNAMODB_ENDPOINT_URL`
- 任意: `CHAT_INFRASTRUCTURE_MODE`、`SIMULATED_LLM_DELAY_SECONDS`
- Boto3認証: 各端末でログイン済みのAWS CLI認証を標準認証チェーンから使用する

## Local Configuration

Create the local environment file and replace the Bedrock identifiers:

```sh
cp .env.example .env
```

バックエンド起動前に、現在ログインしているAWSアカウントを確認する。

```sh
aws sts get-caller-identity
```

AWS CLIの認証方式とログイン操作は各端末の責務とし、`.env`ではAWS認証情報を管理しない。

The local and deployed backends both use the persistent DynamoDB repository.
Deploy the development table and set:

```dotenv
DYNAMODB_CHAT_TABLE_NAME=paperbuddy-dev-chat
DYNAMODB_LIBRARY_TABLE_NAME=paperbuddy-dev-library
```

See `docs/infra/dynamodb.md` for deployment, authentication, and IAM
requirements. The chat table and `gsi1` key schema are defined in
`docs/backend/specification/infrastructure/dynamodb_chat_repository.md`.
The library table is defined in
`docs/backend/specification/infrastructure/dynamodb_indexed_file_catalog.md`.

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
- 認証: `backend/.env`と`frontend/.env`に同じCognito User PoolとWeb App Clientを設定する

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
access_token=replace-with-cognito-access-token

curl --fail-with-body \
  -X POST http://localhost:8000/api/chats \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${access_token}" \
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
