# 実AWS DynamoDB・Bedrock接続確認手順

## 目的

ローカルバックエンドから実AWSのDynamoDBとAmazon Bedrockへ接続し、チャット開始・継続・一覧・履歴取得が正常に動作することを確認する。

## 前提条件

- Docker daemonが起動している
- AWS CLIとAWS Profileが設定済みである
- Bedrock Knowledge Baseが作成・同期済みである
- 対象リージョンで利用モデルへのアクセスが有効である
- AWS ProfileにDynamoDB、Bedrock、CDKデプロイに必要な権限がある

## 1. AWS認証確認

```sh
aws sso login --profile your-profile

AWS_PROFILE=your-profile \
AWS_REGION=ap-northeast-1 \
aws sts get-caller-identity
```

想定したAWSアカウントとIAM Identityが表示されることを確認する。

## 2. Bedrock接続先確認

Knowledge Baseの状態を確認する。

```sh
AWS_PROFILE=your-profile \
AWS_REGION=ap-northeast-1 \
aws bedrock-agent get-knowledge-base \
  --knowledge-base-id your-knowledge-base-id
```

Knowledge Baseの状態が`ACTIVE`であることを確認する。

利用モデルを確認する。

```sh
AWS_PROFILE=your-profile \
AWS_REGION=ap-northeast-1 \
aws bedrock get-foundation-model \
  --model-identifier your-model-id
```

## 3. 開発環境デプロイ

環境変数を設定する。

```sh
export AWS_PROFILE=your-profile
export AWS_REGION=ap-northeast-1
export BEDROCK_KNOWLEDGE_BASE_ID=your-knowledge-base-id
export BEDROCK_MODEL_ARN=arn:aws:bedrock:ap-northeast-1::foundation-model/your-model-id
```

対象アカウント・リージョンでCDKを初めて使用する場合はbootstrapする。

```sh
pnpm -C infra cdk bootstrap
```

開発環境をデプロイする。

```sh
mise run infra:deploy:dev
```

以下のリソースが作成される。

- DynamoDB
- ECS Fargate
- 内部ALB
- 非公開S3
- CloudFront
- VPC・NAT Gateway

AWS利用料金が発生することに注意する。

## 4. ローカルバックエンド設定

`backend/.env`を設定する。

```dotenv
AWS_PROFILE=your-profile
AWS_REGION=ap-northeast-1
DYNAMODB_CHAT_TABLE_NAME=paperbuddy-dev-chat

BEDROCK_KNOWLEDGE_BASE_ID=your-knowledge-base-id
BEDROCK_MODEL_ARN=arn:aws:bedrock:ap-northeast-1::foundation-model/your-model-id
```

フロントエンドとバックエンドを起動する。

```sh
mise run dev
```

## 5. チャット開始確認

チャット開始により、Bedrock呼び出しとDynamoDBへの初回保存を同時に確認する。

```sh
curl --fail-with-body \
  -X POST http://localhost:8000/api/chats \
  -H 'Content-Type: application/json' \
  -H 'X-User-ID: 00000000-0000-0000-0000-000000000001' \
  -d '{"prompt":"登録されている論文について簡潔に説明してください"}'
```

成功レスポンスに含まれる`chat_id`を控える。

## 6. DynamoDB保存確認

`取得したchat_id`を実際の値へ置き換えて実行する。

```sh
AWS_PROFILE=your-profile \
AWS_REGION=ap-northeast-1 \
aws dynamodb query \
  --table-name paperbuddy-dev-chat \
  --key-condition-expression 'pk = :pk' \
  --expression-attribute-values '{
    ":pk": {"S": "CHAT#取得したchat_id"}
  }'
```

以下の項目が取得できることを確認する。

- チャット本体
- ユーザーメッセージ
- LLMメッセージ
- チャット本体に保存されたBedrockの`session_id`

## 7. 一覧・継続・履歴確認

### チャット一覧

```sh
curl --fail-with-body \
  http://localhost:8000/api/chats \
  -H 'X-User-ID: 00000000-0000-0000-0000-000000000001'
```

### チャット継続

```sh
curl --fail-with-body \
  -X POST http://localhost:8000/api/chats/取得したchat_id/messages \
  -H 'Content-Type: application/json' \
  -H 'X-User-ID: 00000000-0000-0000-0000-000000000001' \
  -d '{"prompt":"もう少し詳しく説明してください"}'
```

### メッセージ履歴

```sh
curl --fail-with-body \
  http://localhost:8000/api/chats/取得したchat_id/messages \
  -H 'X-User-ID: 00000000-0000-0000-0000-000000000001'
```

## 8. AWSデプロイ後の疎通確認

CloudFormation Outputの`DistributionDomainName`を確認し、CloudFront経由でアクセスする。

```sh
curl --fail-with-body \
  https://DistributionDomainName/api/health
```

`{"status":"ok"}`が返ることを確認する。

CloudFront経由でも、チャット開始・一覧・継続・履歴取得を同様に確認する。

## 完了条件

- ローカルバックエンドからBedrockの回答を取得できる
- チャット本体とメッセージがDynamoDBへ保存される
- チャット一覧、継続、履歴取得が成功する
- CloudFront経由でフロントエンドとAPIへアクセスできる
- S3とALBへ直接公開アクセスできない

## 次回再開時

作業開始前に以下を実行する。

```sh
mise run backend:test
pnpm -C frontend lint
pnpm -C frontend build
mise run infra:test
AWS_REGION=ap-northeast-1 mise run infra:synth
```

その後、本手順の「1. AWS認証確認」から実AWS接続確認を開始する。

## 実施結果（2026-06-10）

### 完了

- `default`プロファイルでAWS認証を確認した
  - AWSアカウント: `308471217013`
  - IAM Identity: `arn:aws:iam::308471217013:user/ponta-admin`
- `ap-northeast-1`へCDK bootstrapを実施し、`CDKToolkit`の作成が完了した
- `backend/.env`へ`DYNAMODB_CHAT_TABLE_NAME=paperbuddy-dev-chat`を設定した
- Docker daemonの起動を確認した
- 本番用バックエンドDockerイメージのビルドが成功した
- 本番用イメージを非rootユーザー`10001:10001`で起動し、`/api/health`が`{"status":"ok"}`を返すことを確認した
- AWSへ変更を加えない`cdk diff`を実行し、`PaperBuddyDev`の全リソースが新規作成予定であることを確認した
- 生成モデル候補`amazon.nova-lite-v1:0`が`ACTIVE`であることを確認した
- 以下のローカル検証が成功した
  - `mise run backend:test`: 78件成功
  - Domain層・Application層: ブランチカバレッジ100%
  - `pnpm -C frontend lint`: 成功
  - `pnpm -C frontend build`: 成功
  - `mise run infra:test`: 5件成功
  - `AWS_REGION=ap-northeast-1 mise run infra:synth`: 成功

### 未完了・ブロッカー

- `ap-northeast-1`のBedrock Knowledge Base一覧が0件である
- `backend/.env`の以下の値がプレースホルダーのままである
  - `BEDROCK_KNOWLEDGE_BASE_ID=replace-with-knowledge-base-id`
  - `BEDROCK_MODEL_ARN=arn:aws:bedrock:ap-northeast-1::foundation-model/replace-with-model-id`
- `PaperBuddyDev`スタックと`paperbuddy-dev-chat`テーブルは未作成である

### 再開条件

1. `ap-northeast-1`にBedrock Knowledge Baseを作成し、データソースを同期する
2. 利用する生成モデルを決定し、対象モデルへのアクセスを有効にする
3. `backend/.env`のBedrock識別子を実値へ更新する
4. 本手順の「2. Bedrock接続先確認」から再開する
