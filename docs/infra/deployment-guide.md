# AWSデプロイ手順

PaperBuddyの開発環境をAWSへ初回デプロイし、RAG材料PDFをKnowledge Baseへ取り込み、画面から動作確認するまでの手順を定義する。

構成と各AWSリソースの詳細は[Application Deployment](application.md)、ネットワーク構成は[ネットワーク構成](network.md)を参照する。

## デプロイ対象

`PaperBuddyDev`スタックとして、主に以下のリソースを東京リージョンへ作成する。

- CloudFront、非公開フロントエンドS3バケット
- 内部ALB、ECS Fargate
- Cognito User Pool、Web App Client
- DynamoDBチャット・ライブラリテーブル
- Bedrock Knowledge Base、S3 Data Source
- OpenSearch Serverless Vector Search
- RAG材料用非公開S3バケット
- 隔離サブネットを持つVPCとVPC Endpoint

CloudFrontを公開トラフィックの唯一の入口とする。ALBとS3は直接公開しない。

## 着手判断

この手順へ進む前に、以下を満たしていることを確認する。

- AWS CLIで対象アカウントへログイン済みである
- `infra/.env` が用意され、`STACK_NAME`、`AWS_REGION`、`BEDROCK_MODEL_ARN` が正しい
- Docker Desktopが起動できる
- 対象リージョンでBedrockモデルアクセスが有効である

確認コマンド:

```sh
aws sts get-caller-identity
mise run infra:bedrock:check:dev
docker info
```

`infra/.env` の値が不明なまま、または別アカウントに対して進めることは避ける。

## 準備事項

### 必要なツール

- AWS CLI
- Docker Desktop
- mise
- pnpm
- uv

Docker Desktopを起動し、利用できることを確認する。

```sh
docker info
```

miseタスクを確認する。

```sh
mise tasks validate
mise tasks ls --local
```

### CDK bootstrap

対象アカウント・東京リージョンでCDKを初めて使用する場合のみ実行する。

```sh
mise run infra:bootstrap:dev
```

bootstrap済みか確認する場合:

```sh
aws cloudformation describe-stacks \
  --stack-name CDKToolkit \
  --query 'Stacks[0].StackStatus' \
  --output text
```

### 設定ファイル

`infra/.env.example` を `infra/.env` にコピーし、対象アカウント・リージョン・BedrockモデルARNを設定する。

デプロイ実行者には、CloudFormationが各リソースを作成・更新するための権限が必要である。

### Bedrockモデル確認

開発環境の生成モデルARNは`infra/.env`で管理する。`infra:bedrock:check:dev`はそのARNからモデルIDを取り出して利用可否を確認する。

モデルの利用可否を確認する。

```sh
mise run infra:bedrock:check:dev
```

`authorizationStatus`、`entitlementAvailability`、`regionAvailability`が利用可能な状態であることを確認する。

埋め込みモデルにはCDKで`amazon.titan-embed-text-v2:0`を固定設定している。

## デプロイ前検証

リポジトリルートでLintとテストを実行する。

```sh
mise run lint
mise run frontend:test
mise run backend:test
mise run infra:test
```

CloudFormationテンプレートを生成し、構成エラーがないことを確認する。

```sh
mise run infra:synth
```

未コミット差分を確認する。

```sh
git status --short
git diff --check
```

認証先とDockerを確認する。

```sh
aws sts get-caller-identity
docker info --format '{{.ServerVersion}}'
```

## 初回デプロイ

デプロイを実行する。

```sh
mise run infra:deploy:dev
```

確認を求められた場合は、作成されるリソースとIAM変更内容を確認して承認する。

デプロイでは以下が自動実行される。

1. フロントエンドをビルドする
2. バックエンドDockerイメージをビルドしてCDK管理のECRへpushする
3. CloudFormationでAWSリソースを作成・更新する
4. フロントエンド成果物とCognito設定をS3へ配置する
5. CloudFrontキャッシュを無効化する

RAG材料PDFのS3配置とKnowledge Base同期は自動実行されない。

### デプロイ結果の確認

スタック状態を確認する。

```sh
aws cloudformation describe-stacks \
  --stack-name PaperBuddyDev \
  --query 'Stacks[0].StackStatus' \
  --output text
```

`CREATE_COMPLETE`または`UPDATE_COMPLETE`であることを確認する。

CloudFormation Outputを確認する。

```sh
aws cloudformation describe-stacks \
  --stack-name PaperBuddyDev \
  --query 'Stacks[0].Outputs' \
  --output table
```

CloudFront経由でヘルスチェックを実行する。

```sh
distribution_domain_name="$(
    aws cloudformation describe-stacks \
        --stack-name PaperBuddyDev \
        --query "Stacks[0].Outputs[?OutputKey=='DistributionDomainName'].OutputValue | [0]" \
        --output text
)"
curl --fail-with-body "https://${distribution_domain_name}/api/health"
```

期待するレスポンス:

```json
{"status":"ok"}
```

ブラウザで以下へアクセスし、Cognitoのログイン・新規登録画面が表示されることを確認する。

```text
https://<DistributionDomainName>
```

初回利用者はメールアドレスで新規登録し、Cognitoから送信される確認コードで登録を完了する。

### RAG材料PDFの配置

PDFはリポジトリへ置くだけでは取り込まれない。デプロイ完了後、RAG材料用S3バケットの`documents/`配下へアップロードする。

CloudFormation Outputからバケット名を取得する。

```sh
rag_source_bucket_name="$(
    aws cloudformation describe-stacks \
        --stack-name PaperBuddyDev \
        --query "Stacks[0].Outputs[?OutputKey=='RagSourceBucketName'].OutputValue | [0]" \
        --output text
)"
```

単一PDFをアップロードする場合:

```sh
aws s3 cp \
  ./path/to/document.pdf \
  "s3://${rag_source_bucket_name}/documents/document.pdf"
```

ディレクトリ内のPDFを同期する場合:

```sh
aws s3 sync \
  ./path/to/pdfs \
  "s3://${rag_source_bucket_name}/documents/" \
  --exclude '*' \
  --include '*.pdf'
```

アップロード結果を確認する。

```sh
aws s3 ls "s3://${rag_source_bucket_name}/documents/" --recursive
```

### Knowledge Base同期

CloudFormation OutputからKnowledge Base IDとData Source IDを取得する。

```sh
bedrock_knowledge_base_id="$(
    aws cloudformation describe-stacks \
        --stack-name PaperBuddyDev \
        --query "Stacks[0].Outputs[?OutputKey=='BedrockKnowledgeBaseId'].OutputValue | [0]" \
        --output text
)"
bedrock_data_source_id="$(
    aws cloudformation describe-stacks \
        --stack-name PaperBuddyDev \
        --query "Stacks[0].Outputs[?OutputKey=='BedrockDataSourceId'].OutputValue | [0]" \
        --output text
)"
```

同期処理を開始する。

```sh
ingestion_job_id="$(
    aws bedrock-agent start-ingestion-job \
        --knowledge-base-id "$bedrock_knowledge_base_id" \
        --data-source-id "$bedrock_data_source_id" \
        --query 'ingestionJob.ingestionJobId' \
        --output text
)"
```

同期状態を確認する。

```sh
aws bedrock-agent get-ingestion-job \
  --knowledge-base-id "$bedrock_knowledge_base_id" \
  --data-source-id "$bedrock_data_source_id" \
  --ingestion-job-id "$ingestion_job_id" \
  --query 'ingestionJob.{Status:status,Statistics:statistics,FailureReasons:failureReasons}' \
  --output json
```

`Status`が`COMPLETE`になることを確認する。`FAILED`の場合は`FailureReasons`を確認する。

PDFを追加、更新、削除した場合は、S3同期後にKnowledge Base同期を再実行する。

Knowledge Base同期は、ライブラリ一覧用DynamoDBテーブルへPDFメタデータを登録しない。現在の実装では、RAG検索対象への取り込みとライブラリ一覧表示のデータ管理は独立している。

### アプリケーション動作確認

1. CloudFrontドメインへアクセスする
2. Cognitoで新規登録またはログインする
3. チャットでPDF内容に関する質問を送信する
4. 回答が生成され、チャット履歴が再読み込み後も保持されることを確認する

障害時は以下を確認する。

```sh
aws ecs list-clusters --output table

aws cloudformation describe-stack-events \
  --stack-name PaperBuddyDev \
  --max-items 30 \
  --output table
```

ECSやロググループの物理名はCloudFormationまたはAWSコンソールから確認する。

## 差分デプロイ

バックエンド、フロントエンド、インフラ定義を変更した場合:

```sh
mise run lint
mise run frontend:test
mise run backend:test
mise run infra:test
mise run infra:deploy:dev
```

PDFだけを変更した場合、CDKデプロイは不要である。S3への同期とKnowledge Base同期のみ実行する。

### デプロイ失敗時

CloudFormationイベントを確認する。

```sh
aws cloudformation describe-stack-events \
  --stack-name PaperBuddyDev \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`].[Timestamp,LogicalResourceId,ResourceStatusReason]' \
  --output table
```

代表的な確認項目:

- Docker Desktopが起動しているか
- AWS認証の有効期限が切れていないか
- `infra/.env`のリージョンとBedrockモデルARNが正しいか
- Bedrockモデルが対象アカウント・リージョンで利用可能か
- OpenSearch ServerlessやVPC Endpointのクォータに余裕があるか
- 作成しようとしている固定名リソースが既に存在しないか

## 削除と料金

PaperBuddyに起因する課金対象をすべて削除する場合は、[AWS完全削除手順](deletion-guide.md)に従う。

この構成では、特に以下のリソースで継続的な料金が発生する。

- OpenSearch Serverless
- Interface VPC Endpoint
- ECS Fargate
- ALB
- CloudFront
- Bedrockモデル呼び出し

初回デプロイ前に料金を確認すること。

DynamoDBテーブルは削除保護を有効化している。DynamoDBテーブル、S3バケット、Cognito User Poolなど一部リソースには保持ポリシーを設定しているため、スタック削除後も残る場合がある。

保持データや本番相当データを削除する場合は、対象と影響範囲を確認してから個別に実施する。
