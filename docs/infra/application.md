# Application Deployment

ネットワーク構成図は[network.md](network.md)を参照する。
実際の初回デプロイからPDF取り込み、動作確認までの作業手順は[AWSデプロイ手順](deployment-guide.md)を参照する。
PaperBuddyに起因する課金対象を完全に削除する場合は[AWS完全削除手順](deletion-guide.md)を参照する。

## AWS構成

CloudFrontをすべての公開トラフィックの唯一の入口とする。

```text
Browser
  -> CloudFront
       -> default: private S3 bucket
       -> /api/*: CloudFront VPC Origin -> internal ALB -> ECS Fargate
                                                        -> Gateway VPC Endpoints
                                                           -> S3 / DynamoDB
                                                        -> Interface VPC Endpoints
                                                           -> ECR / CloudWatch Logs / Amazon Bedrock / Amazon Cognito

RAG source PDF -> private S3 bucket
```

| 領域 | 構成 |
|---|---|
| 公開入口 | CloudFront |
| フロントエンド | 非公開S3バケット |
| バックエンド | 内部ALB、ECS Fargate |
| ネットワーク | 2 Availability Zoneの隔離サブネット、VPC Endpoint |
| 認証 | Cognito User Pool、Web App Client |
| 永続化 | DynamoDBチャットテーブル、DynamoDBライブラリテーブル |
| RAG材料 | 非公開S3バケットの`documents/`配下 |
| RAG検索 | Bedrock Knowledge Base、OpenSearch Serverless Vector Search |
| LLM | Amazon Bedrockの生成モデル、Titan Text Embeddings V2 |

## 公開範囲

- 利用者はCloudFrontへHTTPSでアクセスする
- フロントエンドS3バケット、RAG材料PDF用S3バケット、ALBは直接公開しない
- `/api/*`はCloudFrontから内部ALB経由でECS Fargateへ転送する
- ECS FargateはVPC Endpoint経由でAWSサービスへ接続する
- 固定AWSアクセスキーは使用せず、ローカルはAWS CLI認証、ECS Fargateはタスクロールを使用する

## 前提条件

- AWS CLIでデプロイ対象アカウントへログイン済みである
- Dockerが起動している
- 対象リージョンでTitan Text Embeddings V2と生成モデルを利用できる
- 対象リージョンでBedrockモデルアクセスが有効である

開発環境のスタック名、リージョン、生成モデルARNは`infra/.env`で管理する。

対象アカウント・リージョンでCDKを初めて使う場合、推奨デプロイタスクがbootstrap済みかを確認し、未実行なら自動でbootstrapする。

```sh
mise run deploy:dev
```

bootstrapだけを個別に実行する場合は次を使う。

```sh
mise run infra:bootstrap:dev
```

## Synthとテスト

`infra:synth`は先にフロントエンドをビルドし、S3へ配置する成果物を含めてCloudFormationテンプレートを生成する。

```sh
mise run infra:test
mise run infra:synth
```

## 開発環境のデプロイ

Knowledge Base、S3 Data Source、生成・埋め込みモデル、Vector StoreはCDKが管理する。デプロイ設定を環境変数で渡す必要はない。

```sh
mise run deploy:dev
```

このコマンドでは、次の処理が自動的に行われる。

1. `infra/.env`、AWS認証先、Docker、Bedrockモデル利用可否を確認する
2. CDK bootstrap済みか確認し、未実行ならbootstrapする
3. Lint、各テスト、CDK synth、`git diff --check`を実行する
4. `frontend/`で`pnpm build`を実行し、`frontend/dist/`を生成する
5. `docker/backend/Dockerfile`からバックエンドのDockerイメージをビルドする
6. DockerイメージをCDK bootstrapが管理するECRアセットリポジトリへpushする
7. ECS Fargateのタスク定義とサービスを、pushしたイメージを参照するよう更新する
8. `frontend/dist/`をフロントエンド配信用S3バケットへ配置する
9. CloudFrontのキャッシュを無効化する
10. Bedrock Knowledge Base、S3 Data Source、OpenSearch Serverless Vector Storeを含むCloudFormationスタック全体を更新する
11. Cognito User PoolとWeb App Clientを作成し、フロントエンド用の`auth-config.json`をS3へ配置する
12. スタック状態、CloudFormation Output、CloudFront経由の`/api/health`を確認する

Knowledge Base IDはCDKが作成したリソースからECSタスク定義へ設定するため、デプロイ時の入力は不要である。埋め込みモデルにはTitan Text Embeddings V2を使用する。

DockerイメージのECRリポジトリ名とタグはCDKがコンテンツハッシュを使用して管理する。通常のデプロイでは、手動の`docker build`、`docker push`、ECRリポジトリ作成は不要である。

フロントエンド配信用S3バケットへの配置もCDKの`BucketDeployment`が行う。通常のデプロイでは、手動の`aws s3 sync frontend/dist ...`は不要である。配置時はバケット内から古い成果物を削除する。

デプロイ完了後、CloudFormation Outputの`DistributionDomainName`へHTTPSでアクセスする。ALBとS3へ直接公開アクセスする経路は作成しない。

Outputは次のコマンドでも確認できる。

```sh
aws cloudformation describe-stacks \
  --stack-name PaperBuddyDev \
  --query 'Stacks[0].Outputs' \
  --output table
```

## RAG材料PDFの配置

RAG材料PDF用S3バケットはCDKデプロイ時に作成されるが、PDFファイルは自動配置されない。

通常運用では、RAG材料PDFを`infra/pdf/[分類]/`配下へ配置し、次のタスクを実行する。

```text
infra/pdf/
  IT/
    RAG Survey.pdf
    RAG Original.pdf
```

```sh
mise run rag:sync:dev
```

このタスクは`infra/pdf/`配下の`*.pdf`を再帰的に走査し、相対パスを保ったままRAG材料用S3バケットの`documents/`配下へ同期する。例えば`infra/pdf/IT/RAG Survey.pdf`は`documents/IT/RAG Survey.pdf`として配置される。S3同期後、ライブラリ一覧用DynamoDBへPDF名、分類、アップロード日時、S3キーを登録し、Bedrock Knowledge Baseのingestion jobを開始して`COMPLETE`まで待機する。

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

ローカルから削除したPDFや分類フォルダ変更で移動したPDFは、`mise run rag:upload:dev`または`mise run rag:sync:dev`実行時にS3の`documents/`配下からも削除される。RAG対象は`infra/pdf/`配下のPDFを正とする。

個別操作が必要な場合は、最初にCloudFormation Outputからバケット名を取得する。

```sh
rag_source_bucket_name="$(
    aws cloudformation describe-stacks \
        --stack-name PaperBuddyDev \
        --query "Stacks[0].Outputs[?OutputKey=='RagSourceBucketName'].OutputValue | [0]" \
        --output text
)"
```

PDFを配置する。

```sh
aws s3 cp ./path/to/document.pdf "s3://${rag_source_bucket_name}/documents/document.pdf"
```

ディレクトリ内のPDFをまとめて同期する場合は次を実行する。

```sh
aws s3 sync ./path/to/pdfs "s3://${rag_source_bucket_name}/documents/" \
  --delete \
  --exclude '*' \
  --include '*.pdf' \
  --include '*.PDF'
```

PDF配置後、個別に同期する場合はCloudFormation OutputからKnowledge Base IDとData Source IDを取得して同期処理を開始する。

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

aws bedrock-agent start-ingestion-job \
  --knowledge-base-id "$bedrock_knowledge_base_id" \
  --data-source-id "$bedrock_data_source_id"
```

PDFを追加、更新した場合は、同じ同期処理を再実行する。

## 更新時のデプロイ

バックエンド、フロントエンド、インフラ定義を変更した場合も同じコマンドを実行する。

```sh
mise run deploy:dev
```

- バックエンドに変更がある場合、Dockerイメージが再ビルド・再pushされ、ECSサービスが更新される
- フロントエンドに変更がある場合、`frontend/dist/`が再配置され、CloudFrontキャッシュが無効化される
- PDFの追加・更新はCDKデプロイとは別に`aws s3 cp`または`aws s3 sync`で行う

## タスクロール権限

Fargateタスクロールには以下の権限だけを付与する。

- DynamoDB: `GetItem`、`Query`、`TransactWriteItems`、`PutItem`、`UpdateItem`、`BatchWriteItem`
- Bedrock: `RetrieveAndGenerate`、`InvokeModel`

## 注意事項

- Interface VPC Endpoint、ALB、Fargate、CloudFront、DynamoDBなどのAWS利用料金が発生する。
- OpenSearch Serverlessは最低稼働コストが発生する。開発環境でも継続課金される点に注意する。
- DynamoDBは削除保護と保持ポリシーを有効にしているため、スタック削除だけでは削除されない。
- S3バケットも保持ポリシーを設定しているため、スタック削除後も残る。
- 現時点では独自ドメインとACM証明書は設定していないため、CloudFront標準ドメインを使用する。
