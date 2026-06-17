# DynamoDB Chat Repository

## 概要

- 接続先・アダプター: Amazon DynamoDB / `DynamoDbChatCommandRepository`、`DynamoDbChatQueryRepository`、`DynamoDbChatTitleRepository`、`DynamoDbChatDeletionRepository`
- 利用目的: チャット本体とチャットメッセージを永続化し、ユーザー別チャット一覧とチャット別メッセージ履歴を取得する

## 対象範囲

### 対象

- チャット本体と初回2メッセージの原子的な新規保存
- チャット本体更新と追加2メッセージの原子的な保存
- 更新バージョンによる楽観排他
- チャットIDを指定したチャット本体の取得
- ユーザー別チャット一覧の最終更新日時降順取得
- 所有ユーザーを検証したチャットメッセージ履歴の発信日時昇順取得
- 所有ユーザーを検証したチャットタイトルの更新
- 所有ユーザーを検証したチャットIDに紐づく全項目の削除

### 対象外

- API利用者がページ単位を指定するページネーション
- DynamoDB Streamsを利用したイベント処理

## 関連する出力ポート

| Protocol | 操作 | 利用ユースケース |
| --- | --- | --- |
| `ChatCommandRepositoryProtocol` | `save_started_chat` | `docs/backend/specification/usecases/chat/start_chat.md` |
| `ChatCommandRepositoryProtocol` | `get_chat` | `docs/backend/specification/usecases/chat/continue_chat.md` |
| `ChatCommandRepositoryProtocol` | `save_exchange` | `docs/backend/specification/usecases/chat/continue_chat.md` |
| `ChatTitleRepositoryProtocol` | `update_title` | `docs/backend/specification/usecases/chat/rename_chat.md` |
| `ChatDeletionRepositoryProtocol` | `delete_chat` | `docs/backend/specification/usecases/chat/delete_chat.md` |
| `ChatQueryRepositoryProtocol` | `list_chats_by_user_id` | `docs/backend/specification/usecases/chat/list_chats.md` |
| `ChatQueryRepositoryProtocol` | `list_messages_by_chat_id` | `docs/backend/specification/usecases/chat/list_chat_messages.md` |

## 接続方式

- SDK・プロトコル: boto3 DynamoDB low-level client
- 接続先: `AWS_REGION`とboto3標準認証情報プロバイダーチェーンで決定する
- 認証方式: ローカルではAWS profile、ECSではタスクロールを使用する。AWSアクセスキーを環境変数やコードへ保存しない
- 必要なIAM操作: テーブルに対する`dynamodb:GetItem`、`dynamodb:Query`、`dynamodb:TransactWriteItems`、`dynamodb:UpdateItem`、`dynamodb:BatchWriteItem`と、`gsi1`に対する`dynamodb:Query`

テーブルは単一テーブル方式とし、以下のキーを持つ。

開発環境のテーブル名は`paperbuddy-dev-chat`とする。CDKでオンデマンド課金、AWS管理暗号化、PITR、削除保護、保持ポリシーを設定する。

`chat_id`は初回登録時にアプリケーションが採番したUUID v7であり、Bedrockが返す識別子は`session_id`属性としてチャット本体に保存する。

| 項目 | `pk` | `sk` | 用途 |
| --- | --- | --- | --- |
| チャット本体 | `CHAT#{chat_id UUID v7}` | `CHAT` | 継続対象チャットの取得、楽観排他更新。`session_id`を属性として保持する |
| メッセージ | `CHAT#{chat_id}` | `MESSAGE#{sent_at}#{request_id}#{sender_order}` | チャット別メッセージ履歴。LLM回答の場合は`citations`をList/Map属性として保持する |

ユーザー別チャット一覧用に、`gsi1`という名前のGSIを使用する。

| 項目 | `gsi1pk` | `gsi1sk` |
| --- | --- | --- |
| チャット本体 | `USER#{user_id}` | `UPDATED#{last_updated_at}#{chat_id}` |

`gsi1`はチャット一覧変換に必要な`chat_id`、`title`、`created_at`、`last_updated_at`を投影する。GSI QueryはDynamoDBの制約により結果整合性となる。チャット本体取得とメッセージ履歴取得は強い整合性で実行する。

## 操作と入出力変換

### save_started_chat

- 内部入力: `Chat`、初回ユーザー`ChatMessage`、初回LLM `ChatMessage`
- 外部入力への変換: UUIDの`chat_id`を文字列化し、`session_id`を独立属性として持つチャット本体1項目とメッセージ2項目を`TransactWriteItems`へ変換する。メッセージ項目には`citations`をList/Map属性として保存する。チャット本体には主キーが未存在である条件式を付ける
- 外部出力: 書き込み成功または`ClientError`
- 内部出力への変換: 成功時は戻り値なし

### get_chat

- 内部入力: `chat_id`
- 外部入力への変換: チャット本体の主キーを指定した強い整合性の`GetItem`
- 外部出力: DynamoDB項目
- 内部出力への変換: UUIDの`chat_id`と文字列の`session_id`を持つ`Chat`へ変換する。所有ユーザー判定はユースケース層で行う

### save_exchange

- 内部入力: 更新済み`Chat`、追加ユーザー`ChatMessage`、追加LLM `ChatMessage`
- 外部入力への変換: チャット本体1項目とメッセージ2項目を`TransactWriteItems`へ変換する。メッセージ項目には`citations`をList/Map属性として保存する。チャット本体には永続化済み`version`が更新前バージョンと一致する条件式を付ける
- 外部出力: 書き込み成功または`ClientError`
- 内部出力への変換: 成功時は戻り値なし

### list_chats_by_user_id

- 内部入力: `user_id`
- 外部入力への変換: `gsi1pk = USER#{user_id}`としてGSIを降順Queryする
- 外部出力: チャット本体項目一覧
- 内部出力への変換: `ChatSummary`のタプルへ変換する

### list_messages_by_chat_id

- 内部入力: `user_id`、`chat_id`
- 外部入力への変換: チャット本体で所有ユーザーを確認後、`pk = CHAT#{chat_id}`かつ`sk begins_with MESSAGE#`として強い整合性のQueryを昇順実行する
- 外部出力: メッセージ項目一覧
- 内部出力への変換: メッセージ本文、発信者、発信日時、`citations`を`ChatMessageRecord`のタプルへ変換する。既存データなどで`citations`属性が存在しない場合は空配列として扱う

### update_title

- 内部入力: `chat_id`、`user_id`、`title`
- 外部入力への変換: チャット本体の主キーを指定し、所有ユーザーが一致する条件付き`UpdateItem`へ変換する
- 内部出力への変換: 成功時は戻り値なし

### delete_chat

- 内部入力: `chat_id`、`user_id`
- 外部入力への変換: チャット本体を強い整合性で取得して所有ユーザーを検証後、`pk = CHAT#{chat_id}`として全ページをQueryし、主キーを25件単位の`BatchWriteItem`削除へ変換する
- 内部出力への変換: 成功時は戻り値なし
- 制約: 複数バッチにまたがる削除は原子的ではない

日時はUTCへ変換したISO 8601文字列として保存する。メッセージ履歴は同一発信日時でもユーザー、LLMの順序で取得できることを保証する。引用情報はDynamoDBのList/Map属性として保存し、JSON文字列化しない。

## エラー変換

| 外部・実装固有の失敗 | 契約上のエラー | 備考 |
| --- | --- | --- |
| 初回保存の条件違反またはその他の`ClientError` | `ChatSaveError` | いずれの項目も保存しない |
| 継続保存のトランザクション条件違反 | `ChatConflictError` | 更新バージョン競合またはメッセージ重複 |
| 継続保存のその他の`ClientError` | `ChatSaveError` | いずれの項目も保存しない |
| 継続対象取得の`ClientError` | `ChatLoadError` | SDKエラーを外部へ漏らさない |
| Query操作の`ClientError` | `RepositoryAccessError` | SDKエラーを外部へ漏らさない |
| タイトル更新の条件違反 | `ChatNotFoundError` | 項目なしまたは所有ユーザー不一致 |
| タイトル更新のその他の`ClientError` | `ChatTitleUpdateError` | SDKエラーを外部へ漏らさない |
| 削除Query・BatchWriteの`ClientError`または未処理項目 | `ChatDeleteError` | SDKエラーを外部へ漏らさない |
| 削除対象の項目なしまたは所有ユーザー不一致 | `ChatNotFoundError` | 対象の存在を他ユーザーへ開示しない |

## 該当データなし

- `get_chat`: 項目なしの場合は`ChatNotFoundError`
- `list_chats_by_user_id`: DynamoDB Queryの全ページを内部で走査し、合計0件の場合は`RepositoryNotFoundError`
- `list_messages_by_chat_id`: DynamoDB Queryの全ページを内部で走査し、チャットなし、所有ユーザー不一致、またはメッセージ合計0件の場合は`RepositoryNotFoundError`
- `delete_chat`: チャットなしまたは所有ユーザー不一致の場合は`ChatNotFoundError`

## タイムアウト・リトライ・制限

- タイムアウト: boto3クライアント設定を使用する。個別値は未確定
- 自動リトライ: boto3クライアント設定を使用し、Repository独自のリトライは行わない
- レート制限・容量制限: DynamoDBの項目サイズ上限と`TransactWriteItems`制限に従う。Queryの1MBページ境界はRepository内部で全ページを走査する

## 設定・機密情報

| 設定項目 | 必須 | 取得元 | 説明 |
| --- | --- | --- | --- |
| `DYNAMODB_CHAT_TABLE_NAME` | DynamoDB利用時は必須 | 環境変数 | チャットテーブル名 |
| `AWS_REGION` | DynamoDB利用時は必須 | 環境変数 | DynamoDBクライアントのリージョン |
| AWS認証情報 | 必須 | boto3標準認証情報プロバイダーチェーン | 実値をコードや環境ファイルへ保存しない |

## クライアントのライフサイクル

- 生成: Dependencies層でboto3 DynamoDBクライアントを生成しRepositoryへ注入する
- 共有範囲: Repositoryとクライアントをアプリケーション単位で共有する
- 破棄: boto3クライアントに明示的な終了処理は不要

## テスト観点

- 正常系: 各Domain型・読み取りモデルとDynamoDB項目の相互変換、トランザクション書き込み、取得順序
- 境界値: 削除対象25件と26件
- 同値クラス: 0件、1件、複数件、同一発信日時のユーザー・LLMメッセージ
- 状態遷移: 更新前バージョン0から更新後バージョン1への楽観排他保存
- 異常系: 該当データなし、所有ユーザー不一致、楽観排他競合、SDKエラー変換

## 関連仕様書

- ユースケース仕様書: `docs/backend/specification/usecases/chat/start_chat.md`
- ユースケース仕様書: `docs/backend/specification/usecases/chat/continue_chat.md`
- ユースケース仕様書: `docs/backend/specification/usecases/chat/list_chats.md`
- ユースケース仕様書: `docs/backend/specification/usecases/chat/list_chat_messages.md`
- ドメイン仕様書: `docs/backend/specification/domain/chat/domain.md`

## 未確定事項

- チャット一覧とメッセージ履歴のページネーション方式
- DynamoDBクライアントの接続・読み取りタイムアウト値
