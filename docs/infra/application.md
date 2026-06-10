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
- RAG材料: 非公開S3バケットへPDFを配置する。Bedrock Knowledge Baseとの接続は後続実装とする

固定AWSアクセスキーは使用しない。ローカルのCDK実行はAWS Profile、Fargateはタスクロールを使用する。

## 前提条件

- AWS CLIとAWS Profileが設定済みである
- Dockerが起動している
- Bedrock Knowledge Base IDと利用するモデルARNが分かっている
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

Bedrock識別子を環境変数で渡してデプロイする。識別子はCloudFormationパラメータとしてECSタスク定義へ設定され、コードには保存されない。

```sh
export AWS_PROFILE=your-profile
export AWS_REGION=ap-northeast-1
export BEDROCK_KNOWLEDGE_BASE_ID=your-knowledge-base-id
export BEDROCK_MODEL_ARN=arn:aws:bedrock:ap-northeast-1::foundation-model/your-model-id

mise run infra:deploy:dev
```

デプロイ完了後、CloudFormation Outputの`DistributionDomainName`へHTTPSでアクセスする。ALBとS3へ直接公開アクセスする経路は作成しない。

## タスクロール権限

Fargateタスクロールには以下の権限だけを付与する。

- DynamoDB: `GetItem`、`Query`、`TransactWriteItems`
- Bedrock: `RetrieveAndGenerate`、`InvokeModel`

ECSタスクへ`AWS_PROFILE`や固定AWSアクセスキーは設定しない。

## 注意事項

- Interface VPC Endpoint、ALB、Fargate、CloudFront、DynamoDBなどのAWS利用料金が発生する。
- DynamoDBは削除保護と保持ポリシーを有効にしているため、スタック削除だけでは削除されない。
- S3バケットも保持ポリシーを設定しているため、スタック削除後も残る。
- RAG材料用S3バケットはバージョニングを有効にしている。
- 現時点では独自ドメインとACM証明書は設定していないため、CloudFront標準ドメインを使用する。
