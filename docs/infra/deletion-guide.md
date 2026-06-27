# AWS完全削除手順

PaperBuddyのAWSリソースを削除し、PaperBuddyに起因する継続課金を停止するための手順を定義する
この手順は、チャット履歴、RAG材料PDF、Cognito利用者、ログを含むデータを完全に削除する。
バックアップを残さないため、必要なデータを退避してから実行する。

## 削除対象

- OpenSearch Serverless Collection
- ECS Fargateサービス・クラスター
- 内部ALB
- CloudFront Distribution
- Interface VPC Endpoint
- VPC
- Bedrock Knowledge Base・Data Source
- DynamoDBチャットテーブル
- DynamoDBライブラリテーブル
- フロントエンド配信用S3バケット
- RAG材料用S3バケットとオブジェクトバージョン
- Cognito User Pool
- CloudWatch Logsロググループ

CDK bootstrap資産はPaperBuddy本体の削除手順には含めない。
このAWSアカウント・リージョンの`CDKToolkit`をPaperBuddy専用として扱える場合にだけ、別手順で削除する。
他プロジェクトとCDK bootstrapを共有している場合は、bootstrap削除タスクを実行しない。

## 削除可否の確認

この手順へ進む前に、以下を満たしていることを確認する。

- PaperBuddy関連リソースをすべて削除してよい
- 削除対象アカウントとリージョンが正しい
- 必要なデータはすでに退避済み、または退避不要である
- AWS CLIで対象アカウントへログイン済みである

## 削除前準備

AWS CLIによるログインが完了していることを確認する
```sh
aws sts get-caller-identity
```

必要に応じて、削除前にRAG材料PDFやDynamoDBデータを退避する
```sh
rag_source_bucket_name="$(
  aws cloudformation describe-stacks \
    --stack-name PaperBuddyDev \
    --query "Stacks[0].Outputs[?OutputKey=='RagSourceBucketName'].OutputValue | [0]" \
    --output text
)"

aws s3 sync \
  "s3://${rag_source_bucket_name}/documents/" \
  ./backup/paperbuddy-documents/
```

DynamoDBのオンデマンドバックアップを作成する場合、バックアップ自体も削除するまで課金対象となる。

## 削除手順

リポジトリルートで次を実行する。
```sh
mise run infra:destroy:dev
```

このタスクは削除前にAWSアカウント、リージョン、スタック名、保持リソース名、OpenSearch Serverless Collection名、Bedrock Knowledge Base IDを表示し、続行確認としてスタック名の入力を求める。
表示された対象を確認し、削除してよい場合だけスタック名を入力する。

削除を続行すると、以下を順に実行する。

1. `infra/.env`から`STACK_NAME`と`AWS_REGION`を読み込む
2. CloudFormation Outputとスタックリソース一覧を一時ファイルへ保存する
3. CloudFormationスタックを削除する
4. Bedrock Knowledge BaseとData Sourceが残っている場合は削除する
5. OpenSearch Serverless Collection、Access Policy、Security Policyが残っている場合は削除する
6. 保持されたDynamoDBテーブルの削除保護を解除して削除する
7. 保持されたS3バケットの通常オブジェクト、全バージョン、削除マーカーを削除してからバケットを削除する
8. 保持されたCognito User Poolを削除する
9. スタックリソースとPaperBuddy名プレフィックスに基づいてCloudWatch Logsロググループを削除する
10. PaperBuddy本体リソースが残っていないことをサービス別に監査する

CDK bootstrap資産も削除する場合は、本体削除後に次を実行する。
他プロジェクトと共有していないことを確認できる場合だけ実行する。

```sh
mise run infra:destroy:bootstrap:dev
```

このタスクは、CDK bootstrap S3バケット、CDK bootstrap ECRリポジトリとDockerイメージ、`CDKToolkit`スタックを削除する。

## 削除後の確認

タスクは削除結果を監査し、対象リソースが残っている場合は失敗する。追加で確認する場合は、削除漏れ監査タスクを実行する。

```sh
mise run infra:audit:deletion:dev
```

このタスクは、CloudFormationスタック、PaperBuddyタグ付きリソース、OpenSearch Serverless、Bedrock Knowledge Base、DynamoDB、S3、CloudWatch Logs、ECS、ELB、VPC、VPC Endpoint、CloudFront、Cognito、CDK bootstrap資産を一覧する。
手動で確認する場合は、スタックとPaperBuddyタグ付きリソースを確認する。

```sh
aws cloudformation describe-stacks \
  --stack-name PaperBuddyDev

aws cloudformation describe-stacks \
  --stack-name CDKToolkit

aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=aws:cloudformation:stack-name,Values=PaperBuddyDev \
  --query 'ResourceTagMappingList[].ResourceARN' \
  --output table
```

`describe-stacks`は対象スタックが存在しないエラーになることを期待する。
タグ付きリソースが出力された場合は、サービス種別と課金有無を確認して個別削除する。

削除に失敗した場合は、CloudFormationイベントを確認する。

```sh
aws cloudformation describe-stack-events \
  --stack-name PaperBuddyDev \
  --query 'StackEvents[?ResourceStatus==`DELETE_FAILED`].[Timestamp,LogicalResourceId,ResourceStatusReason]' \
  --output table
```

`FORCE_DELETE_STACK`は、原因を確認せずに使用しない。強制削除では課金対象リソースが残る可能性がある。

## 課金停止の確認

AWS Cost Explorerの反映には時間差がある。削除直後に利用料金が表示されても、削除前の利用分である可能性がある。
削除後24時間から48時間を目安に、以下のサービスの新規利用が増えていないことを確認する。

- Amazon OpenSearch Service
- Amazon Virtual Private Cloud
- Amazon Elastic Container Service
- Elastic Load Balancing
- Amazon CloudFront
- Amazon DynamoDB
- Amazon S3
- Amazon CloudWatch
- Amazon Bedrock
- Amazon Elastic Container Registry

Cost Explorerや請求画面で継続的な課金が残る場合は、対象サービスのリソース一覧をリージョンごとに確認する。
