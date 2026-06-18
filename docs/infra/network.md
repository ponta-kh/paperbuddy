# ネットワーク構成

## 構成図

編集可能なdraw.io形式の構成図を使用する。

- [network.drawio](network.drawio)
- diagrams.netまたはdraw.ioデスクトップアプリで開く
- AWS公式Architecture Iconsのdraw.io組み込みAWS4ライブラリを使用する

## 通信経路

| 通信元 | 通信先 | 経路・制約 |
|---|---|---|
| 利用者 | CloudFront | HTTPS。CloudFrontを唯一の公開入口とする |
| CloudFront | フロントエンドS3 | Origin Access Control経由 |
| CloudFront | 内部ALB | `/api/*`のみCloudFront VPC Origin経由で転送 |
| 内部ALB | ECS Fargate | TCP 8000。ECS Security GroupはALB Security Groupからのみ許可 |
| ECS Fargate | DynamoDB / S3 | Gateway VPC Endpoint経由で通信 |
| ECS Fargate | ECR / CloudWatch Logs / Bedrock / Cognito | Interface VPC Endpoint経由でHTTPS通信 |

## セキュリティ境界

- ALBは内部向けとしてプライベートApplicationサブネットへ配置する。
- ECS FargateはプライベートApplicationサブネットへ配置し、Public IPを付与しない。
- VPCにはNAT Gatewayとインターネットへの外向き経路を持たせない。
- フロントエンドS3とRAG材料PDF用S3は公開アクセスをすべて遮断する。
- ECSタスクには固定AWSアクセスキーを設定せず、タスクロールを使用する。
- RAG材料PDF用S3はBedrock Knowledge BaseのS3 Data Sourceとして接続する。
- Bedrock Knowledge BaseのVector StoreにはOpenSearch Serverlessを使用する。

## 現在の制約

- Interface VPC Endpointは2 Availability Zoneへ配置するため、Endpointサービスごとに各AZの時間料金が発生する。
- 外部インターネットへの接続が必要になった場合は、許可する通信経路を別途設計する必要がある。
- 独自ドメイン、ACM証明書、AWS WAFは未構築である。
