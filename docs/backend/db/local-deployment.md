# DynamoDBローカルデプロイ

ローカル開発ではDocker ComposeでDynamoDB Localを起動し、バックエンドから同じRepository実装で接続する。AWS上のDynamoDBとの差分は接続先、認証情報、テーブル名だけとし、テーブル構造とデータ形式は[DynamoDBスキーマ](shema.md)に従う。

## 起動方法

リポジトリルートで次を実行する。

```sh
mise run dev
```

バックエンドとDynamoDB Localだけを起動する場合は次を使用する。

```sh
mise run dev:backend
```

## テーブル作成

DynamoDB LocalのテーブルはDocker Composeの`dynamodb-init`サービスが作成する。既に存在する場合は再作成しない。

作成するテーブルは次のとおりである。

| 用途 | ローカルテーブル名 |
|---|---|
| チャット | `paperbuddy-local-chat` |
| ライブラリ一覧 | `paperbuddy-local-library` |

チャットテーブルには`gsi1`も作成する。スキーマは[DynamoDBスキーマ](shema.md)に従う。

## 環境変数

Docker ComposeではDynamoDB Local向けに次の環境変数を設定する。

```dotenv
AWS_REGION=ap-northeast-1
AWS_ACCESS_KEY_ID=local
AWS_SECRET_ACCESS_KEY=local
DYNAMODB_CHAT_TABLE_NAME=paperbuddy-local-chat
DYNAMODB_LIBRARY_TABLE_NAME=paperbuddy-local-library
DYNAMODB_ENDPOINT_URL=http://dynamodb-local:8000
```

バックエンドは`DYNAMODB_ENDPOINT_URL`が設定されている場合、DynamoDB Localへ接続する。

## データ保持と初期化

DynamoDB LocalのデータはDocker Volumeに保存する。ローカルデータを初期化する場合は次を実行する。

```sh
docker compose -f docker/compose.yaml down --volumes
```

## 注意事項

- ローカル起動ではDynamoDB Localを使用するため、DynamoDBのAWS利用料金は発生しない。
- ローカル認証情報はDynamoDB Local用のダミー値であり、AWS認証には使用しない。
- 自動テストは実AWSへ接続せず、DynamoDBクライアントをスタブ化する。
