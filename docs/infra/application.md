# Application Deployment

ネットワーク構成図は[network.md](network.md)を参照する。

## 構成

CloudFrontをすべての公開トラフィックの唯一の入口とする。

```text
Browser
  -> CloudFront
       -> default: private S3 bucket
       -> /api/*: CloudFront VPC Origin -> internal ALB -> ECS Fargate
                                                        -> Gateway VPC Endpoints
                                                           -> S3 / DynamoDB
                                                        -> Interface VPC Endpoints
                                                           -> ECR / CloudWatch Logs / Amazon Bedrock

RAG source PDF -> private S3 bucket
```

- フロントエンド: 非公開S3バケットへ配置し、CloudFront Origin Access Control経由だけで配信する
- バックエンド: プライベートサブネットのECS Fargateで起動する
- ALB: 内部向けとしてプライベートサブネットに配置する
- CloudFront: `/api/*`をキャッシュせず、VPC Origin経由でALBへ転送する
- VPC: 2 Availability Zoneの隔離サブネット。NAT GatewayとInternet Gatewayは作成しない
- AWSサービス接続: S3・DynamoDBのGateway Endpointと、ECR・CloudWatch Logs・BedrockのInterface Endpointを使用する
- 永続化: 開発用DynamoDBテーブル`paperbuddy-dev-chat`
- ライブラリ一覧: 開発用DynamoDBテーブル`paperbuddy-dev-library`
- RAG材料: 非公開S3バケットの`documents/`配下へPDFを配置し、Bedrock Knowledge BaseのS3 Data Sourceとして使用する
- Vector Store: 非公開のOpenSearch Serverless Vector Searchコレクションを使用する

固定AWSアクセスキーは使用しない。ローカルのCDK実行はAWS Profile、Fargateはタスクロールを使用する。

## 前提条件

- AWS CLIとAWS Profileが設定済みである
- Dockerが起動している
- 利用する生成モデルARNが分かっている
- 対象リージョンでTitan Text Embeddings V2と生成モデルを利用できる
- 対象リージョンでBedrockモデルアクセスが有効である

対象アカウント・リージョンでCDKを初めて使う場合は、最初にbootstrapする。

```sh
AWS_PROFILE=your-profile AWS_REGION=ap-northeast-1 pnpm -C infra cdk bootstrap
```

## Synthとテスト

`infra:synth`は先にフロントエンドをビルドし、S3へ配置する成果物を含めてCloudFormationテンプレートを生成する。

```sh
mise run infra:test
AWS_PROFILE=your-profile AWS_REGION=ap-northeast-1 mise run infra:synth
```

## 開発環境のデプロイ

生成モデルARNを環境変数で渡してデプロイする。Knowledge Base、S3 Data Source、埋め込みモデル、Vector StoreはCDKが管理する。

```sh
export AWS_PROFILE=your-profile
export AWS_REGION=ap-northeast-1
export BEDROCK_MODEL_ARN=arn:aws:bedrock:ap-northeast-1::foundation-model/your-model-id

mise run infra:deploy:dev
```

このコマンドでは、次の処理が自動的に行われる。

1. `frontend/`で`pnpm build`を実行し、`frontend/dist/`を生成する
2. `backend/Dockerfile`からバックエンドのDockerイメージをビルドする
3. DockerイメージをCDK bootstrapが管理するECRアセットリポジトリへpushする
4. ECS Fargateのタスク定義とサービスを、pushしたイメージを参照するよう更新する
5. `frontend/dist/`をフロントエンド配信用S3バケットへ配置する
6. CloudFrontのキャッシュを無効化する
7. Bedrock Knowledge Base、S3 Data Source、OpenSearch Serverless Vector Storeを含むCloudFormationスタック全体を更新する

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

最初にCloudFormation Outputからバケット名を取得する。

```sh
export RAG_SOURCE_BUCKET_NAME="$(
  aws cloudformation describe-stacks \
    --stack-name PaperBuddyDev \
    --query "Stacks[0].Outputs[?OutputKey=='RagSourceBucketName'].OutputValue | [0]" \
    --output text
)"
```

PDFを配置する。

```sh
aws s3 cp ./path/to/document.pdf "s3://${RAG_SOURCE_BUCKET_NAME}/documents/document.pdf"
```

ディレクトリ内のPDFをまとめて同期する場合は次を実行する。

```sh
aws s3 sync ./path/to/pdfs "s3://${RAG_SOURCE_BUCKET_NAME}/documents/" \
  --exclude '*' \
  --include '*.pdf'
```

PDF配置後、CloudFormation OutputからKnowledge Base IDとData Source IDを取得して同期処理を開始する。

```sh
export BEDROCK_KNOWLEDGE_BASE_ID="$(
  aws cloudformation describe-stacks \
    --stack-name PaperBuddyDev \
    --query "Stacks[0].Outputs[?OutputKey=='BedrockKnowledgeBaseId'].OutputValue | [0]" \
    --output text
)"
export BEDROCK_DATA_SOURCE_ID="$(
  aws cloudformation describe-stacks \
    --stack-name PaperBuddyDev \
    --query "Stacks[0].Outputs[?OutputKey=='BedrockDataSourceId'].OutputValue | [0]" \
    --output text
)"

aws bedrock-agent start-ingestion-job \
  --knowledge-base-id "$BEDROCK_KNOWLEDGE_BASE_ID" \
  --data-source-id "$BEDROCK_DATA_SOURCE_ID"
```

PDFを追加、更新、削除した場合は、同じ同期処理を再実行する。

## 更新時のデプロイ

バックエンド、フロントエンド、インフラ定義を変更した場合も同じコマンドを実行する。

```sh
mise run infra:deploy:dev
```

- バックエンドに変更がある場合、Dockerイメージが再ビルド・再pushされ、ECSサービスが更新される
- フロントエンドに変更がある場合、`frontend/dist/`が再配置され、CloudFrontキャッシュが無効化される
- PDFの追加・更新はCDKデプロイとは別に`aws s3 cp`または`aws s3 sync`で行う

## タスクロール権限

Fargateタスクロールには以下の権限だけを付与する。

- DynamoDB: `GetItem`、`Query`、`TransactWriteItems`
- Bedrock: `RetrieveAndGenerate`、`InvokeModel`

ECSタスクへ`AWS_PROFILE`や固定AWSアクセスキーは設定しない。

## 注意事項

- Interface VPC Endpoint、ALB、Fargate、CloudFront、DynamoDBなどのAWS利用料金が発生する。
- OpenSearch Serverlessは最低稼働コストが発生する。開発環境でも継続課金される点に注意する。
- DynamoDBは削除保護と保持ポリシーを有効にしているため、スタック削除だけでは削除されない。
- S3バケットも保持ポリシーを設定しているため、スタック削除後も残る。
- RAG材料用S3バケットはバージョニングを有効にしている。
- 現時点では独自ドメインとACM証明書は設定していないため、CloudFront標準ドメインを使用する。
