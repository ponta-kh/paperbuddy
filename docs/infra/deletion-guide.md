# AWS完全削除手順

PaperBuddyのAWSリソースを削除し、PaperBuddyに起因する継続課金を停止するための手順を定義する。

この手順は、チャット履歴、RAG材料PDF、Cognito利用者、ログを含むデータを完全に削除する。削除後は復元できないため、必要なデータを退避してから実行する。

## 削除対象

`PaperBuddyDev`スタックを削除すると、主に以下の課金対象はCloudFormationによって削除される。

- OpenSearch Serverless Collection
- ECS Fargateサービス・クラスター
- 内部ALB
- CloudFront Distribution
- Interface VPC Endpoint
- VPC
- Bedrock Knowledge Base・Data Source

以下は保持ポリシーまたは削除保護により、スタック削除後も残るため個別削除が必要である。

- DynamoDBチャットテーブル
- DynamoDBライブラリテーブル
- フロントエンド配信用S3バケット
- RAG材料用S3バケットとオブジェクトバージョン
- Cognito User Pool
- CloudWatch Logsロググループ

CDK bootstrapのアセットS3バケットとECRリポジトリにも、デプロイしたファイルやDockerイメージが残る。これらを削除する方法は、CDK bootstrapを他プロジェクトと共有しているかによって異なる。

## 削除可否の確認

この手順へ進む前に、以下を満たしていることを確認する。

- PaperBuddy関連リソースをすべて削除してよい
- 削除対象アカウントとリージョンが正しい
- 必要なデータはすでに退避済み、または退避不要である
- AWS CLIで対象アカウントへログイン済みである

削除後は復元できない。必要なデータがある場合は、先に退避する。

## 削除前準備

各端末でAWS CLIによるログインが完了していることを前提とする。AWS認証情報やProfileはこの手順では設定しない。
削除対象のスタック名とリージョンは`infra/.env`の`STACK_NAME`、`AWS_REGION`から取得するため、削除用の環境変数をコンソールやシェルへ手動登録する必要はない。

通常の削除は次のコマンドだけで実行する。

```sh
mise run infra:destroy:dev
```

このタスクは削除前にAWSアカウント、リージョン、スタック名、保持リソース名を表示し、続行確認としてスタック名の入力を求める。削除してよい対象であることを必ず確認する。

タスク実行前に認証先だけ確認したい場合は、任意で次を実行する。

```sh
aws sts get-caller-identity
```

削除を続行すると、以下を順に実行する。

1. `infra/.env`から`STACK_NAME`と`AWS_REGION`を読み込む
2. CloudFormation Outputとスタックリソース一覧を一時ファイルへ保存する
3. CloudFormationスタックを削除する
4. 保持されたDynamoDBテーブルの削除保護を解除して削除する
5. 保持されたS3バケットの通常オブジェクト、全バージョン、削除マーカーを削除してからバケットを削除する
6. 保持されたCognito User Poolを削除する
7. 保持されたCloudWatch Logsロググループを削除する
8. PaperBuddy本体リソースが残っていないことを監査する

このタスクはCDK bootstrap資産を削除しない。CDK bootstrap資産は他プロジェクトと共有される可能性があるため、後述の「CDK bootstrapアセットの削除」を確認して個別に実行する。

### 手動分解手順で実行する場合

以下は`mise run infra:destroy:dev`が内部で行う処理を分解した手順である。通常は実行不要である。途中から再開する場合や失敗調査を行う場合に使用する。

以下のコマンドは同じbashセッションで順番に実行する。

```sh
bash
```

リージョンとスタック名を`infra/.env`から読み込み、削除対象アカウントを確認する。

```sh
AWS_REGION="$(
  awk -F= '
    $0 !~ /^[[:space:]]*#/ && $1 == "AWS_REGION" {
      sub(/^[^=]*=/, "")
      gsub(/^[[:space:]]+|[[:space:]]+$/, "")
      gsub(/^["'\''"]|["'\''"]$/, "")
      print
      exit
    }
  ' infra/.env
)"

STACK_NAME="$(
  awk -F= '
    $0 !~ /^[[:space:]]*#/ && $1 == "STACK_NAME" {
      sub(/^[^=]*=/, "")
      gsub(/^[[:space:]]+|[[:space:]]+$/, "")
      gsub(/^["'\''"]|["'\''"]$/, "")
      print
      exit
    }
  ' infra/.env
)"

aws sts get-caller-identity
printf 'AWS_REGION=%s\n' "$AWS_REGION"
printf 'STACK_NAME=%s\n' "$STACK_NAME"
```

スタック状態を確認する。

```sh
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --query 'Stacks[0].StackStatus' \
  --output text
```

### 必要なデータのバックアップ

必要に応じて、RAG材料PDFをローカルへ退避する。

```sh
RAG_SOURCE_BUCKET_NAME="$(
  aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='RagSourceBucketName'].OutputValue | [0]" \
    --output text
)"

aws s3 sync \
  "s3://${RAG_SOURCE_BUCKET_NAME}/documents/" \
  ./backup/paperbuddy-documents/
```

DynamoDBデータのバックアップが必要な場合は、オンデマンドバックアップを作成する。ただし、バックアップも削除するまで課金対象となる。

```sh
aws dynamodb create-backup \
  --table-name paperbuddy-dev-chat \
  --backup-name paperbuddy-dev-chat-final-backup

aws dynamodb create-backup \
  --table-name paperbuddy-dev-library \
  --backup-name paperbuddy-dev-library-final-backup
```

継続課金を完全に停止する場合、確認完了後にこれらのバックアップも削除する。

### 保持リソースIDの保存

スタック削除後はCloudFormation Outputやスタックリソース一覧を取得できないため、削除前に保存する。

```sh
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --output json \
  > /tmp/paperbuddy-stack.json

aws cloudformation list-stack-resources \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --output json \
  > /tmp/paperbuddy-stack-resources.json
```

保持リソースIDを環境変数と配列へ設定する。

```sh
output_value() {
  jq -r --arg key "$1" \
    '.Stacks[0].Outputs[] | select(.OutputKey == $key) | .OutputValue' \
    /tmp/paperbuddy-stack.json
}

CHAT_TABLE_NAME="$(output_value ChatTableName)"
LIBRARY_TABLE_NAME="$(output_value LibraryTableName)"
FRONTEND_BUCKET_NAME="$(output_value FrontendBucketName)"
RAG_SOURCE_BUCKET_NAME="$(output_value RagSourceBucketName)"
USER_POOL_ID="$(output_value UserPoolId)"

mapfile -t LOG_GROUP_NAMES < <(
  jq -r '
    .StackResourceSummaries[]
    | select(.ResourceType == "AWS::Logs::LogGroup")
    | .PhysicalResourceId
  ' /tmp/paperbuddy-stack-resources.json
)
```

削除対象を確認する。

```sh
printf 'CHAT_TABLE_NAME=%s\n' "$CHAT_TABLE_NAME"
printf 'LIBRARY_TABLE_NAME=%s\n' "$LIBRARY_TABLE_NAME"
printf 'FRONTEND_BUCKET_NAME=%s\n' "$FRONTEND_BUCKET_NAME"
printf 'RAG_SOURCE_BUCKET_NAME=%s\n' "$RAG_SOURCE_BUCKET_NAME"
printf 'USER_POOL_ID=%s\n' "$USER_POOL_ID"
printf 'LOG_GROUP_NAMES=%s\n' "${LOG_GROUP_NAMES[*]}"
```

## 削除作業

### PaperBuddyDevスタックの削除

CloudFormationでスタックを削除する。保持ポリシーが設定されたリソースは残る。

```sh
aws cloudformation delete-stack \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION"

aws cloudformation wait stack-delete-complete \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION"
```

削除に失敗した場合は、イベントを確認する。

```sh
aws cloudformation describe-stack-events \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --query 'StackEvents[?ResourceStatus==`DELETE_FAILED`].[Timestamp,LogicalResourceId,ResourceStatusReason]' \
  --output table
```

`FORCE_DELETE_STACK`は、原因を確認せずに使用しない。強制削除では課金対象リソースが残る可能性がある。

### 保持されたDynamoDBテーブルの削除

DynamoDBテーブルは削除保護が有効なため、削除保護を解除してから削除する。

```sh
for TABLE_NAME in "$CHAT_TABLE_NAME" "$LIBRARY_TABLE_NAME"; do
  aws dynamodb update-table \
    --table-name "$TABLE_NAME" \
    --region "$AWS_REGION" \
    --no-deletion-protection-enabled

  until [ "$(
    aws dynamodb describe-table \
      --table-name "$TABLE_NAME" \
      --region "$AWS_REGION" \
      --query 'Table.TableStatus' \
      --output text
  )" = "ACTIVE" ]; do
    sleep 5
  done

  aws dynamodb delete-table \
    --table-name "$TABLE_NAME" \
    --region "$AWS_REGION"

  aws dynamodb wait table-not-exists \
    --table-name "$TABLE_NAME" \
    --region "$AWS_REGION"
done
```

オンデマンドバックアップを作成した場合、不要になったバックアップも削除する。

```sh
aws dynamodb list-backups \
  --region "$AWS_REGION" \
  --table-name "$CHAT_TABLE_NAME" \
  --output table

aws dynamodb list-backups \
  --region "$AWS_REGION" \
  --table-name "$LIBRARY_TABLE_NAME" \
  --output table
```

バックアップARNを確認してから削除する。

```sh
aws dynamodb delete-backup \
  --region "$AWS_REGION" \
  --backup-arn <削除対象バックアップARN>
```

### 保持されたS3バケットの削除

RAG材料用S3バケットではバージョニングが有効なため、現行オブジェクトだけでなく全バージョンと削除マーカーを削除する必要がある。

以下の関数は、通常オブジェクト、全バージョン、削除マーカーを削除する。

```sh
empty_s3_bucket_completely() {
  local bucket_name="$1"
  local delete_payload
  local object_count

  aws s3 rm "s3://${bucket_name}" --recursive --region "$AWS_REGION"

  while true; do
    delete_payload="$(
      aws s3api list-object-versions \
        --bucket "$bucket_name" \
        --region "$AWS_REGION" \
        --max-items 1000 \
        --output json \
      | jq -c '{
          Objects: (
            [.Versions[]?, .DeleteMarkers[]?]
            | map({Key: .Key, VersionId: .VersionId})
          ),
          Quiet: true
        }'
    )"

    object_count="$(jq '.Objects | length' <<< "$delete_payload")"
    [ "$object_count" -eq 0 ] && break

    aws s3api delete-objects \
      --bucket "$bucket_name" \
      --region "$AWS_REGION" \
      --delete "$delete_payload" \
      > /dev/null
  done
}
```

フロントエンド配信用S3バケットとRAG材料用S3バケットを空にして削除する。

```sh
for BUCKET_NAME in "$FRONTEND_BUCKET_NAME" "$RAG_SOURCE_BUCKET_NAME"; do
  empty_s3_bucket_completely "$BUCKET_NAME"

  aws s3api delete-bucket \
    --bucket "$BUCKET_NAME" \
    --region "$AWS_REGION"
done
```

### 保持されたCognito User Poolの削除

Cognito利用者を含むUser Poolを削除する。

```sh
aws cognito-idp delete-user-pool \
  --user-pool-id "$USER_POOL_ID" \
  --region "$AWS_REGION"
```

### 保持されたCloudWatch Logsの削除

スタック削除後も保持されたロググループを削除する。

```sh
for LOG_GROUP_NAME in "${LOG_GROUP_NAMES[@]}"; do
  aws logs delete-log-group \
    --log-group-name "$LOG_GROUP_NAME" \
    --region "$AWS_REGION"
done
```

### CDK bootstrapアセットの削除

CDK bootstrapのS3バケットとECRリポジトリには、デプロイ時のファイル・Dockerイメージが残り、ストレージ料金が発生する可能性がある。

### 他プロジェクトとCDK bootstrapを共有する場合

`CDKToolkit`スタック自体は削除しない。まず、参照されていないアセット候補を表示する。

```sh
pnpm -C infra cdk gc \
  "aws://$(aws sts get-caller-identity --query Account --output text)/${AWS_REGION}" \
  --unstable=gc \
  --action print \
  --type all \
  --created-buffer-days 0 \
  --rollback-buffer-days 0
```

表示内容を確認し、削除して問題ないアセットだけであることを確認してから実行する。

```sh
pnpm -C infra cdk gc \
  "aws://$(aws sts get-caller-identity --query Account --output text)/${AWS_REGION}" \
  --unstable=gc \
  --action full \
  --type all \
  --created-buffer-days 0 \
  --rollback-buffer-days 0
```

`cdk gc`はCDK環境内の未参照アセットを対象とする。他プロジェクトが使用するアセットを誤削除しないよう、必ず`--action print`の結果を確認する。

### CDK bootstrapがPaperBuddy専用の場合

このAWSアカウント・リージョンで他のCDKプロジェクトが`CDKToolkit`を使用していない場合のみ、bootstrap資産とスタックを削除する。

bootstrapのS3バケット名とECRリポジトリ名を取得する。

```sh
CDK_ASSET_BUCKET_NAME="$(
  aws cloudformation describe-stacks \
    --stack-name CDKToolkit \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue | [0]" \
    --output text
)"

CDK_ASSET_REPOSITORY_NAME="$(
  aws cloudformation describe-stacks \
    --stack-name CDKToolkit \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='ImageRepositoryName'].OutputValue | [0]" \
    --output text
)"
```

bootstrapのS3アセットを削除する。

```sh
empty_s3_bucket_completely "$CDK_ASSET_BUCKET_NAME"
```

bootstrapのECRイメージを削除する。

```sh
while true; do
  IMAGE_IDS="$(
    aws ecr list-images \
      --repository-name "$CDK_ASSET_REPOSITORY_NAME" \
      --region "$AWS_REGION" \
      --max-results 100 \
      --query 'imageIds' \
      --output json
  )"

  [ "$(jq 'length' <<< "$IMAGE_IDS")" -eq 0 ] && break

  aws ecr batch-delete-image \
    --repository-name "$CDK_ASSET_REPOSITORY_NAME" \
    --region "$AWS_REGION" \
    --image-ids "$IMAGE_IDS" \
    > /dev/null
done
```

`CDKToolkit`スタックを削除する。

```sh
aws cloudformation delete-stack \
  --stack-name CDKToolkit \
  --region "$AWS_REGION"

aws cloudformation wait stack-delete-complete \
  --stack-name CDKToolkit \
  --region "$AWS_REGION"
```

### 削除結果の監査

`PaperBuddyDev`スタックが存在しないことを確認する。

```sh
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION"
```

`Stack with id PaperBuddyDev does not exist`となることを確認する。

保持リソースが存在しないことを確認する。各コマンドは対象が存在しないエラーになることを期待する。

```sh
aws dynamodb describe-table \
  --table-name "$CHAT_TABLE_NAME" \
  --region "$AWS_REGION"

aws dynamodb describe-table \
  --table-name "$LIBRARY_TABLE_NAME" \
  --region "$AWS_REGION"

aws s3api head-bucket --bucket "$FRONTEND_BUCKET_NAME"
aws s3api head-bucket --bucket "$RAG_SOURCE_BUCKET_NAME"

aws cognito-idp describe-user-pool \
  --user-pool-id "$USER_POOL_ID" \
  --region "$AWS_REGION"
```

ロググループが存在しないことを確認する。

```sh
for LOG_GROUP_NAME in "${LOG_GROUP_NAMES[@]}"; do
  aws logs describe-log-groups \
    --log-group-name-prefix "$LOG_GROUP_NAME" \
    --region "$AWS_REGION" \
    --query 'logGroups[].logGroupName' \
    --output text
done
```

OpenSearch Serverless Collectionが存在しないことを確認する。

```sh
aws opensearchserverless list-collections \
  --region "$AWS_REGION" \
  --collection-filters name=paperbuddy-dev-kb \
  --query 'collectionSummaries' \
  --output json
```

`[]`となることを確認する。

PaperBuddyDevスタックのタグが残るリソースを確認する。

```sh
aws resourcegroupstaggingapi get-resources \
  --region "$AWS_REGION" \
  --tag-filters Key=aws:cloudformation:stack-name,Values=PaperBuddyDev \
  --query 'ResourceTagMappingList[].ResourceARN' \
  --output table
```

出力されたリソースがある場合は、サービス種別と課金有無を確認して個別削除する。

### 課金停止の確認

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
