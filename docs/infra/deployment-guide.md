# AWSデプロイ手順

PaperBuddyの開発環境をAWSへ初回デプロイし、RAG材料PDFをKnowledge Baseへ取り込み、画面から動作確認するまでの手順を定義する。

この文書は作業手順だけを扱う。構成や設計判断は[アプリケーション構成](application.md)、ネットワーク詳細は[ネットワーク構成](network.md)、DynamoDB詳細は[DynamoDB構成](dynamodb.md)を参照する。

## この手順で作成する主なリソース

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

## 準備事項

### 着手前確認

この手順へ進む前に、以下を満たしていることを確認する。

- AWS CLIで対象アカウントへログイン済みである
- `infra/.env` が用意され、`STACK_NAME`、`AWS_REGION`、`BEDROCK_GENERATION_MODEL_IDENTIFIER` が正しい
- Docker Desktopが起動できる
- 対象リージョンでBedrockモデルアクセスが有効である
  `authorizationStatus`、`entitlementAvailability`、`regionAvailability`が利用可能な状態であることを確認する

```sh
aws sts get-caller-identity
mise run infra:bedrock:check:dev
docker info
```

### CDK bootstrap

対象アカウント・東京リージョンでCDKを初めて使用する場合のみ実行する。

```sh
mise run infra:bootstrap:dev
```

bootstrap済みか確認するコマンド:

```sh
aws cloudformation describe-stacks \
  --stack-name CDKToolkit \
  --query 'Stacks[0].StackStatus' \
  --output text
```

### 定義情報

対象アカウント・リージョン・Bedrock生成モデル: `infra/.env` 
埋め込みモデル: AWS CDK定義ファイル内（`amazon.titan-embed-text-v2:0`を固定設定）

## 推奨デプロイ手順

開発環境の通常デプロイは、リポジトリルートで次の統合タスクを実行する。

```sh
mise run deploy:dev
```

このタスクは次を順に実行する。

1. `infra/.env`の必須値を確認する
2. miseタスク定義、AWS認証先、Docker、Bedrockモデル利用可否を確認する
3. CDK bootstrap済みか確認し、未実行の場合は`infra:bootstrap:dev`を実行する
4. Lint、各テスト、CDK synth、`git diff --check`を実行する
5. `infra:deploy:dev`でAWSへデプロイする
6. スタック状態、CloudFormation Output、CloudFront経由の`/api/health`を確認する

PDFのS3配置とKnowledge Base同期は、この統合タスクでは実行しない。

## 個別検証手順

問題切り分けや部分実行が必要な場合は、以下の個別コマンドを使用する。

### ソース検証

各ディレクトリ内のソースを対象に、Format、Lint、テストを実行する
```sh
mise run format
mise run lint
mise run frontend:test
mise run backend:test
mise run infra:test
```

### CloudFormationテンプレート検証

構成エラーがないことを確認する。
```sh
mise run infra:synth
```

### 未コミット差分を確認

```sh
git status --short
git diff --check
```

## 個別デプロイ

事前検証やbootstrapを個別に済ませている場合は、デプロイだけを実行できる。

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

初回利用者はメールアドレスで新規登録し、Cognitoから送信される確認コードで登録を完了する。

### RAG材料PDFの配置

RAG材料PDFは`infra/pdf/[分類]/`配下に配置する。デプロイ完了後、次のタスクでRAG材料用S3バケットの`documents/`配下へ同期し、Knowledge Base同期を開始する。

```text
infra/pdf/
  IT/
    RAG Survey.pdf
    RAG Original.pdf
```

```sh
mise run rag:sync:dev
```

このタスクは次を順に実行する。

1. `infra/pdf/`配下の`*.pdf`を再帰的に走査し、相対パスを保ったままRAG材料用S3バケットの`documents/`配下へ同期する
2. 同期後のS3オブジェクト一覧を表示する
3. ライブラリ一覧用DynamoDBへPDF名、分類、アップロード日時、S3キーを登録する
4. Bedrock Knowledge Baseのingestion jobを開始する
5. ingestion jobの状態を確認し、`COMPLETE`まで待機する

S3へのアップロードだけを実行する場合:

```sh
mise run rag:upload:dev
```

このタスクもS3同期後にライブラリ一覧用DynamoDBを同期する。

ライブラリ一覧用DynamoDBの同期だけを実行する場合:

```sh
mise run rag:catalog:sync:dev
```

Knowledge Base同期だけを実行する場合:

```sh
mise run rag:generate:dev
```

PDFを追加、更新、削除、分類フォルダ移動した場合は、同じタスクを再実行する。
ローカルから削除したPDFや分類フォルダ変更で移動したPDFは、S3の`documents/`配下からも削除される。RAG対象は`infra/pdf/`配下のPDFを正とする。

Knowledge Base同期は、ライブラリ一覧用DynamoDBテーブルへPDFメタデータを登録しない。現在の実装では、RAG検索対象への取り込みとライブラリ一覧表示のデータ管理は独立している。

### RAG材料PDFの個別操作

問題切り分けや手動操作が必要な場合は、CloudFormation Outputからバケット名を取得する。

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
  --delete \
  --exclude '*' \
  --include '*.pdf' \
  --include '*.PDF'
```

アップロード結果を確認する。

```sh
aws s3 ls "s3://${rag_source_bucket_name}/documents/" --recursive
```

### Knowledge Base同期の個別操作

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
