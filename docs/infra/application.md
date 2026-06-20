# アプリケーション構成

PaperBuddyをAWS開発環境へ配置するための構成、責務分担、設計上の制約を定義する。

実際の作業手順は次を参照する。

- 完全初回デプロイ、差分デプロイ、PDF取り込み、動作確認: [AWSデプロイ手順](deployment-guide.md)
- 完全削除と課金停止確認: [AWS完全削除手順](deletion-guide.md)
- ネットワーク詳細: [ネットワーク構成](network.md)
- DynamoDBデプロイ時の扱い: [DynamoDB構成](dynamodb.md)
- DynamoDBスキーマ: [DynamoDBスキーマ](../backend/db/shema.md)

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

## RAG材料PDFの配置

RAG材料PDF用S3バケットはCDKデプロイ時に作成されるが、PDFファイルは自動配置されない。

通常運用では、RAG材料PDFを`infra/pdf/[分類]/`配下へ配置する。

```text
infra/pdf/
  IT/
    RAG Survey.pdf
    RAG Original.pdf
```

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
