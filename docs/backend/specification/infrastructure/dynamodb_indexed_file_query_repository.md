# DynamoDbIndexedFileQueryRepository 外部接続仕様書

## 1. 概要

- 対象: RAG取り込み済みデータソース一覧
- 目的: DynamoDBから一覧を取得し、Application層へ読み取り専用モデルを返す

## 2. 設定

- `AWS_REGION`: 接続先リージョン
- `DYNAMODB_LIBRARY_TABLE_NAME`: データソース一覧テーブル名
- `DYNAMODB_ENDPOINT_URL`: ローカルモード時のみ利用
- `CHAT_INFRASTRUCTURE_MODE`: `local` の場合は `DYNAMODB_ENDPOINT_URL` を使う。チャット生成先の切り替えには使用しない

## 3. テーブル前提

- テーブルはデータソース情報を保持している
- 主キーは `pk` / `sk` を使用する
- レコードには少なくとも次の属性を持つ
  - `source_id`
  - `s3_key`
  - `paper_title`
  - `category`
  - `status`
  - `s3_uploaded_at`
  - `rag_indexed_at` は任意属性とし、存在しない場合は未設定として扱う

## 4. 取得方式

- `Scan` で全件取得する
- 1MBを超える場合はページネーションを継続する
- 取得後にApplication層で `category`、`paper_title` の昇順へ整列する

## 5. 変換ルール

- `source_id` は `UUID` に変換する
- `s3_uploaded_at` と `rag_indexed_at` はタイムゾーン付き日時に変換する
- `rag_indexed_at` が存在しない場合は `null` とする

## 6. エラー変換

- DynamoDBのクライアントエラーは `RepositoryAccessError` に変換する
- 取得件数が0件の場合は `RepositoryNotFoundError` を送出する
- 変換不能なレスポンスは `RepositoryAccessError` に変換する

## 7. 検証観点

- 正常系: 1件、複数件、ページネーションあり
- 代替系: 0件
- 異常系: クライアントエラー、属性欠落、型不整合
