# チャットタイトル変更ユースケース仕様書

## 概要

認証済みユーザーが所有するチャットのタイトルを変更する。

## 入力

- `user_id`: 認証済みユーザーID
- `chat_id`: 変更対象チャットの識別子。UUID v7
- `title`: 変更後のタイトル

タイトルの文字数、空白、整形に関する業務制約は未確定のため、本ユースケースでは新しい制約を追加しない。

## 正常系

1. `chat_id`と`user_id`を指定して、チャットタイトルを更新する。
2. 更新した`chat_id`と`title`を返す。

## 使用するポート

| Protocol | 操作 | 用途 | 送出する可能性のあるエラー |
| --- | --- | --- | --- |
| `ChatTitleRepositoryProtocol` | `update_title` | 所有ユーザーに紐づくチャットタイトルを更新する | `ChatNotFoundError`, `ChatTitleUpdateError` |

## 異常系

- 対象チャットが存在しない、または別ユーザーが所有する場合は`ChatNotFoundError`を送出する。
- タイトルを更新できない場合は`ChatTitleUpdateError`を送出する。

## API

- `PATCH /api/chats/{chat_id}`
- 成功時: `200 OK`
