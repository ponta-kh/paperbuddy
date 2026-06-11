# DynamoDB Development Environment

## 方針

ローカルバックエンドとECS上のバックエンドは、同じDynamoDBテーブル群と実AWSの開発用DynamoDBテーブルを使用する。

- テーブル名: `paperbuddy-dev-chat`
- ライブラリ一覧テーブル名: `paperbuddy-dev-library`
- リージョン: 既定値は`ap-northeast-1`
- ローカル認証: boto3標準認証チェーンのAWS Profile
- ECS認証: ECSタスクロール
- 課金モード: オンデマンド
- 保護: AWS管理暗号化、PITR、削除保護、CloudFormation削除時の保持

ローカルとAWS上で異なるのは認証方式だけであり、Repository実装、テーブル、データ形式は共通となる。

## 初回デプロイ

AWSアクセスキーは`.env`へ保存せず、AWS SSOなどでProfileを設定する。

```sh
aws sso login --profile your-profile
AWS_PROFILE=your-profile AWS_REGION=ap-northeast-1 mise run infra:synth
```

対象アカウント・リージョンでCDKを初めて使う場合は、デプロイ前に次を実行する。

```sh
AWS_PROFILE=your-profile AWS_REGION=ap-northeast-1 pnpm -C infra cdk bootstrap
```

削除保護と保持ポリシーを有効にしているため、`cdk destroy`だけではテーブルを削除できない。

アプリケーションを含むデプロイ手順は[AWSデプロイ手順](deployment-guide.md)を参照する。

## ローカル接続

`backend/.env`を次のように設定し、`mise run dev`でフロントエンドとバックエンドを起動する。

```dotenv
AWS_PROFILE=your-profile
AWS_REGION=ap-northeast-1
DYNAMODB_CHAT_TABLE_NAME=paperbuddy-dev-chat
DYNAMODB_LIBRARY_TABLE_NAME=paperbuddy-dev-library
```

ローカルで使用するAWS Profileには、テーブルに対する次の権限が必要となる。

- `dynamodb:GetItem`
- `dynamodb:Query`
- `dynamodb:Scan`
- `dynamodb:TransactWriteItems`

`dynamodb:Query`のResourceには、テーブル本体に加えて`paperbuddy-dev-chat/index/gsi1`を含める。
`dynamodb:Scan`のResourceには`paperbuddy-dev-library`を含める。

## ECS接続

ECSデプロイ時はコンテナへ次の環境変数を設定する。

```dotenv
AWS_REGION=ap-northeast-1
DYNAMODB_CHAT_TABLE_NAME=paperbuddy-dev-chat
DYNAMODB_LIBRARY_TABLE_NAME=paperbuddy-dev-library
```

`AWS_PROFILE`や固定AWSアクセスキーは設定しない。ECSタスクロールへ必要なDynamoDB権限を付与する。

## 注意事項

- 実AWSのDynamoDBを使用するため、ローカル実行でもAWS利用料金が発生する。
- 開発者間で同じテーブルとデータを共有する。テストデータはユーザーIDを分けて識別する。
- 自動テストは実AWSへ接続せず、DynamoDBクライアントをスタブ化する。
