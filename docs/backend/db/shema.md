# DynamoDBスキーマ

PaperBuddyが使用するDynamoDBテーブルのスキーマを定義する。

## チャットテーブル

### テーブルキー

| 項目 | 型 | 用途 |
|---|---|---|
| `pk` | String | パーティションキー |
| `sk` | String | ソートキー |

### GSI

| インデックス | 項目 | 型 | 用途 |
|---|---|---|---|
| `gsi1` | `gsi1pk` | String | ユーザー単位のチャット一覧取得用パーティションキー |
| `gsi1` | `gsi1sk` | String | 最終更新日時降順取得用ソートキー |

`gsi1`のProjectionは`INCLUDE`とし、次の属性を投影する。

- `chat_id`
- `title`
- `created_at`
- `last_updated_at`

### チャット本体項目

| 項目 | 型 | 値 |
|---|---|---|
| `pk` | String | `CHAT#{chat_id}` |
| `sk` | String | `CHAT` |
| `entity_type` | String | `chat` |
| `chat_id` | String | チャットID。UUID v7 |
| `session_id` | String | Bedrock会話セッションID |
| `title` | String | チャットタイトル |
| `user_id` | String | 所有ユーザーID |
| `created_at` | String | UTCのISO 8601日時 |
| `last_updated_at` | String | UTCのISO 8601日時 |
| `version` | Number | 楽観ロック用バージョン |
| `gsi1pk` | String | `USER#{user_id}` |
| `gsi1sk` | String | `UPDATED#{last_updated_at}#{chat_id}` |

### チャットメッセージ項目

| 項目 | 型 | 値 |
|---|---|---|
| `pk` | String | `CHAT#{chat_id}` |
| `sk` | String | `MESSAGE#{sent_at}#{request_id}#{sender_order}` |
| `entity_type` | String | `message` |
| `chat_id` | String | チャットID。UUID v7 |
| `request_id` | String | チャットターンID。UUID v7 |
| `sender` | String | `user`または`llm` |
| `content` | String | メッセージ本文 |
| `citations` | List | 引用情報 |
| `sent_at` | String | UTCのISO 8601日時 |

`sender_order`は同一発信日時でもユーザーメッセージ、LLM回答の順に取得するための値とする。ユーザー送信は`0`、LLM回答は`1`を使用する。

### 引用情報

`citations`はDynamoDBのList/Map属性として保存し、JSON文字列化しない。

| 項目 | 型 | 値 |
|---|---|---|
| `text` | String | 引用テキスト |
| `span_start` | Number | 回答本文内の開始位置 |
| `span_end` | Number | 回答本文内の終了位置 |
| `sources` | List | 引用元一覧 |

`sources`の各要素は次のMap属性を持つ。

| 項目 | 型 | 値 |
|---|---|---|
| `content` | String | 引用元内容 |
| `location_type` | String | 引用元位置種別 |
| `uri` | String | 引用元URI |
| `metadata` | Map | 引用元メタデータ |

## ライブラリテーブル

### テーブルキー

| 項目 | 型 | 用途 |
|---|---|---|
| `pk` | String | パーティションキー |
| `sk` | String | ソートキー |

### 論文ソース項目

| 項目 | 型 | 値 |
|---|---|---|
| `pk` | String | `SOURCE#{source_id}` |
| `sk` | String | `SOURCE` |
| `source_id` | String | S3キーから生成したUUID v5 |
| `s3_key` | String | RAG材料PDFのS3キー。`documents/[分類]/[ファイル名]` |
| `paper_title` | String | 論文名。拡張子`.pdf`は含めない |
| `category` | String | `infra/pdf/[分類]/`の分類名 |
| `status` | String | `uploaded` |
| `s3_uploaded_at` | String | S3アップロード日時。UTCのISO 8601日時 |
| `rag_indexed_at` | String \| Null | RAG取り込み日時。未設定可 |
