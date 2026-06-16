#!/bin/sh
set -eu

endpoint_url="${DYNAMODB_ENDPOINT_URL:?DYNAMODB_ENDPOINT_URL は必須です}"
region="${AWS_REGION:-ap-northeast-1}"
chat_table="${DYNAMODB_CHAT_TABLE_NAME:?DYNAMODB_CHAT_TABLE_NAME は必須です}"
library_table="${DYNAMODB_LIBRARY_TABLE_NAME:?DYNAMODB_LIBRARY_TABLE_NAME は必須です}"

aws_dynamodb() {
  aws dynamodb --endpoint-url "$endpoint_url" --region "$region" "$@"
}

wait_for_dynamodb() {
  attempt=1
  while [ "$attempt" -le 30 ]; do
    if aws_dynamodb list-tables >/dev/null 2>&1; then
      return 0
    fi

    attempt=$((attempt + 1))
    sleep 1
  done

  echo "DynamoDB Localが起動しませんでした" >&2
  return 1
}

create_chat_table() {
  if aws_dynamodb describe-table --table-name "$chat_table" >/dev/null 2>&1; then
    echo "チャットテーブルは作成済みです: $chat_table"
    return 0
  fi

  aws_dynamodb create-table \
    --table-name "$chat_table" \
    --attribute-definitions \
      AttributeName=pk,AttributeType=S \
      AttributeName=sk,AttributeType=S \
      AttributeName=gsi1pk,AttributeType=S \
      AttributeName=gsi1sk,AttributeType=S \
    --key-schema \
      AttributeName=pk,KeyType=HASH \
      AttributeName=sk,KeyType=RANGE \
    --global-secondary-indexes '[{"IndexName":"gsi1","KeySchema":[{"AttributeName":"gsi1pk","KeyType":"HASH"},{"AttributeName":"gsi1sk","KeyType":"RANGE"}],"Projection":{"ProjectionType":"INCLUDE","NonKeyAttributes":["chat_id","title","created_at","last_updated_at"]},"ProvisionedThroughput":{"ReadCapacityUnits":5,"WriteCapacityUnits":5}}]' \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 >/dev/null

  aws_dynamodb wait table-exists --table-name "$chat_table"
  echo "チャットテーブルを作成しました: $chat_table"
}

create_library_table() {
  if aws_dynamodb describe-table --table-name "$library_table" >/dev/null 2>&1; then
    echo "ライブラリテーブルは作成済みです: $library_table"
    return 0
  fi

  aws_dynamodb create-table \
    --table-name "$library_table" \
    --attribute-definitions \
      AttributeName=pk,AttributeType=S \
      AttributeName=sk,AttributeType=S \
    --key-schema \
      AttributeName=pk,KeyType=HASH \
      AttributeName=sk,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 >/dev/null

  aws_dynamodb wait table-exists --table-name "$library_table"
  echo "ライブラリテーブルを作成しました: $library_table"
}

wait_for_dynamodb
create_chat_table
create_library_table
