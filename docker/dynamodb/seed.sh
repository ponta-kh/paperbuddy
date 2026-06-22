#!/bin/sh
set -eu

endpoint_url="${DYNAMODB_ENDPOINT_URL:?DYNAMODB_ENDPOINT_URL は必須です}"
region="${AWS_REGION:-ap-northeast-1}"
library_table="${DYNAMODB_LIBRARY_TABLE_NAME:?DYNAMODB_LIBRARY_TABLE_NAME は必須です}"

aws_dynamodb() {
  aws dynamodb --endpoint-url "$endpoint_url" --region "$region" "$@"
}

put_seed_item() {
  source_id="$1"
  item="$2"

  aws_dynamodb put-item \
    --table-name "$library_table" \
    --item "$item" >/dev/null
  echo "ライブラリ初期データを登録または更新しました: $source_id"
}

put_seed_item "81967935-8cc7-5059-bc7e-4587e1f6ae16" '{
  "pk": {"S": "SOURCE#81967935-8cc7-5059-bc7e-4587e1f6ae16"},
  "sk": {"S": "SOURCE"},
  "source_id": {"S": "81967935-8cc7-5059-bc7e-4587e1f6ae16"},
  "s3_key": {"S": "documents/cs/attention-is-all-you-need.pdf"},
  "paper_title": {"S": "Attention Is All You Need"},
  "category": {"S": "cs"},
  "status": {"S": "uploaded"},
  "s3_uploaded_at": {"S": "2026-01-10T00:00:00Z"},
  "rag_indexed_at": {"S": "2026-01-10T00:10:00Z"}
}'

put_seed_item "ee20f38b-9597-59b8-a0bc-32748ecd23b6" '{
  "pk": {"S": "SOURCE#ee20f38b-9597-59b8-a0bc-32748ecd23b6"},
  "sk": {"S": "SOURCE"},
  "source_id": {"S": "ee20f38b-9597-59b8-a0bc-32748ecd23b6"},
  "s3_key": {"S": "documents/ml/retrieval-augmented-generation.pdf"},
  "paper_title": {"S": "Retrieval-Augmented Generation"},
  "category": {"S": "ml"},
  "status": {"S": "uploaded"},
  "s3_uploaded_at": {"S": "2026-01-11T00:00:00Z"},
  "rag_indexed_at": {"S": "2026-01-11T00:15:00Z"}
}'

put_seed_item "580740e7-4354-581c-9fc7-46cbc11932de" '{
  "pk": {"S": "SOURCE#580740e7-4354-581c-9fc7-46cbc11932de"},
  "sk": {"S": "SOURCE"},
  "source_id": {"S": "580740e7-4354-581c-9fc7-46cbc11932de"},
  "s3_key": {"S": "documents/nlp/bert-pre-training.pdf"},
  "paper_title": {"S": "BERT Pre-training"},
  "category": {"S": "nlp"},
  "status": {"S": "uploaded"},
  "s3_uploaded_at": {"S": "2026-01-12T00:00:00Z"},
  "rag_indexed_at": {"S": "2026-01-12T00:20:00Z"}
}'
