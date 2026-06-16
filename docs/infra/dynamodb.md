# DynamoDB Development Environment

## 方針

ECS上のバックエンドは、AWS上の開発用DynamoDBテーブルを使用する。
ローカルバックエンドはDocker Composeで起動するDynamoDB Localを使用する。
どちらも同じRepository実装とデータ形式を使用し、接続先だけを環境変数で切り替える。

- テーブル名: `paperbuddy-dev-chat`
- ライブラリ一覧テーブル名: `paperbuddy-dev-library`
- リージョン: 既定値は`ap-northeast-1`
- ローカル認証: DynamoDB Local用の固定ダミー認証情報
- ECS認証: ECSタスクロール
- 課金モード: オンデマンド
- 保護: AWS管理暗号化、PITR、削除保護、CloudFormation削除時の保持

ローカルとAWS上で異なるのは接続先と認証方式であり、Repository実装、テーブル構造、データ形式は共通となる。

## 初回デプロイ

AWSアクセスキーは`.env`へ保存しない。各端末でAWS CLIによるログインが完了していることを前提とする。

```sh
aws sts get-caller-identity
mise run infra:synth
```

対象アカウント・リージョンでCDKを初めて使う場合は、デプロイ前に次を実行する。

```sh
mise run infra:bootstrap:dev
```

削除保護と保持ポリシーを有効にしているため、`cdk destroy`だけではテーブルを削除できない。

アプリケーションを含むデプロイ手順は[AWSデプロイ手順](deployment-guide.md)を参照する。

## ローカル接続

`docker/.env`へCognitoの識別子を設定し、`mise run dev`でフロントエンドとバックエンドを起動する。
DynamoDB LocalのテーブルはDocker Composeの`dynamodb-init`サービスが作成する。

```dotenv
AWS_REGION=ap-northeast-1
COGNITO_USER_POOL_ID=ap-northeast-1_replace-with-user-pool-id
COGNITO_USER_POOL_CLIENT_ID=replace-with-user-pool-client-id
```

ローカル起動時はDynamoDB Localへ接続するため、DynamoDB用のAWS IAM権限は不要となる。

## ECS接続

ECSデプロイ時はコンテナへ次の環境変数を設定する。

```dotenv
AWS_REGION=ap-northeast-1
DYNAMODB_CHAT_TABLE_NAME=paperbuddy-dev-chat
DYNAMODB_LIBRARY_TABLE_NAME=paperbuddy-dev-library
```

`AWS_PROFILE`や固定AWSアクセスキーは設定しない。ECSタスクロールへ必要なDynamoDB権限を付与する。

## 注意事項

- ローカル起動ではDynamoDB Localを使用するため、DynamoDBのAWS利用料金は発生しない。
- ローカルデータはDocker Volumeへ保存する。初期化する場合は`docker compose -f docker/compose.yaml down --volumes`を実行する。
- 自動テストは実AWSへ接続せず、DynamoDBクライアントをスタブ化する。
