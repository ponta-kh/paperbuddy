# PaperBuddy Backend

## Prerequisites

- Python 3.14 and uv
- Docker
- Cognito User PoolとWeb App Clientを作成済みであること

AWSアクセスキーは`.env`へ保存しない。

アプリケーション固有の環境変数は
`src/dependencies/settings.py`のPydantic Settingsへ集約している。

- 共通必須: `AWS_REGION`、`DYNAMODB_CHAT_TABLE_NAME`、`DYNAMODB_LIBRARY_TABLE_NAME`
- 認証必須: `COGNITO_USER_POOL_ID`、`COGNITO_USER_POOL_CLIENT_ID`
- AWSモード必須: `BEDROCK_KNOWLEDGE_BASE_ID`、`BEDROCK_MODEL_ARN`
- ローカルモード必須: `DYNAMODB_ENDPOINT_URL`
- 任意: `CHAT_INFRASTRUCTURE_MODE`、`SIMULATED_LLM_DELAY_SECONDS`

## Local Configuration

Docker Composeで起動する場合は、`docker/.env`へCognitoの識別子を設定する。

ローカル環境とデプロイ環境は、どちらも永続化用のDynamoDB Repository実装を使用する。
ローカルのDocker Composeでは、同じRepository実装の接続先をDynamoDB Localへ切り替える。

DynamoDBのデプロイ、認証、IAM要件は`docs/infra/dynamodb.md`を参照する。
デプロイ環境のチャットテーブルと`gsi1`のキー構造は
`docs/backend/specification/infrastructure/dynamodb_chat_repository.md`に記載している。
ライブラリ一覧テーブルは
`docs/backend/specification/infrastructure/dynamodb_indexed_file_catalog.md`に記載している。

## ローカル全体動作確認

実AWSへ接続せずに画面から一連のチャット操作を確認する場合は、リポジトリルートで
以下を実行する。

```sh
mise run dev
```

- バックエンド: `http://localhost:8000`
- フロントエンド: `http://localhost:5173`
- DB: DynamoDB Localコンテナ。データはDocker Volumeへ保存する
- DynamoDB Localのテーブル作成: Docker Composeの`dynamodb-init`サービス
- LLM: 既定で2秒待機し、300文字の疑似回答を返す
- 初期データ: なし
- 認証: `docker/.env`と`frontend/.env`に同じCognito User PoolとWeb App Clientを設定する

`CHAT_INFRASTRUCTURE_MODE=local`の場合だけローカル用LLMを注入する。
DynamoDB RepositoryはAWSデプロイ時と同じ実装を使用し、接続先だけDynamoDB Localへ切り替える。

バックエンドとDynamoDB Localを停止する場合は以下を実行する。

```sh
docker compose -f docker/compose.yaml down
```

DynamoDB Localの保存データも初期化する場合は、`--volumes`を追加する。

## 自動テスト

ドメイン層とユースケース層のカバレッジ条件を含めて、バックエンドテストを実行する。

```sh
mise run backend:test
```

- `backend:test:domain`は、実行可能なDomainコードに対してstatementとbranchの100%カバレッジを要求する。
- `backend:test:application`は、出力ポートをモック化してユースケースをテストし、statementとbranchの100%カバレッジを要求する。
- Repository Protocol宣言は実行可能なドメイン振る舞いを持たないため、実行時カバレッジの対象外とする。
