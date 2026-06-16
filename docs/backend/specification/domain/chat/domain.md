# Chat ドメインモデル仕様書

## 1. 概要

- 目的: ユーザーに紐づくチャットとそのやり取りを表現し、LLMへ渡すプロンプトが常に有効かつ整形済みであることを保証する

## 2. 対象範囲

### 対象

- アプリケーションが採番するチャットID、外部会話を継続するためのセッションID、タイトル、所有ユーザーID、作成日時、最終更新日時を持つチャット
- チャット内のユーザーとLLMによるやり取り
- やり取りの発信者、内容、発信日時
- プロンプトの不正入力チェック、文字数チェック、整形

### 対象外

- LLMまたはRAGによる回答生成
- LLMまたはRAGへの接続方法
- チャットの取得、開始、会話継続などのユースケース処理手順
- 認証方式
- 永続化方式

## 3. 用語

| 用語 | 定義 |
| --- | --- |
| チャット | 1人のユーザーに紐づく会話単位 |
| チャットID | アプリケーションが初回登録時に採番するUUID v7形式のチャット識別子 |
| セッションID | チャット生成サービス上の会話を継続するために保持する外部識別子 |
| チャットメッセージ | チャット内でユーザーまたはLLMが発信した1件の内容 |
| チャットターン | ユーザーの質問と、それに対するLLM回答を1対1で関連付けた会話の1往復 |
| 発信者 | チャットメッセージを発信した主体。ユーザーまたはLLMのいずれか |
| プロンプト | ユーザーがLLMへ渡すために入力した内容。検証および整形の対象となる |
| 正常回答日時 | LLMから正常な回答を受領した時点で記録する日時 |
| 作成日時 | チャット開始時にLLMから正常な回答が返された日時 |
| 最終更新日時 | チャットで最後にLLMから正常な回答が返された日時 |

## 4. 同一トランザクションで保証する整合性

チャット本体は全メッセージ履歴を保持しない。チャットで正常なLLM回答を受け取った場合、以下を同一トランザクションで保存する。

- ユーザーが発信したチャットメッセージ
- LLMが正常に返したチャットメッセージ
- LLM回答の発信日時で更新された`Chat.last_updated_at`

初回チャット開始時は、上記に加えて新しい`Chat`本体を同一トランザクションで保存する。保存処理の一部が失敗した場合は、すべてのローカル変更をロールバックする。

チャットメッセージは件数上限がなく、全履歴を取得するのは過去チャット参照ユースケースに限られるため、`Chat`本体には保持しない。

## 5. Entity・Domainオブジェクト

### Chat

- 種別: Entity
- 識別子: `chat_id`。初回登録時にアプリケーションが採番するUUID v7
- 責務: ユーザーに紐づくチャットを表現し、チャットID、セッションID、タイトル、所有ユーザーID、作成日時、最終更新日時の整合性を保証する

#### 属性

| 属性名 | 型 | 必須 | 説明・制約 |
| --- | --- | --- | --- |
| `chat_id` | UUID v7 | 必須 | アプリケーション内でチャットを一意に識別する値 |
| `session_id` | `str` | 必須 | チャット生成サービス上の会話を継続する識別子。空文字および空白文字のみは不可 |
| `title` | `str` | 必須 | チャットのタイトル。詳細な制約は未確定 |
| `user_id` | UUID | 必須 | チャットを所有するユーザーの識別子 |
| `created_at` | タイムゾーンを含む日時 | 必須 | チャット開始時にLLMから正常な回答が返された日時 |
| `last_updated_at` | タイムゾーンを含む日時 | 必須 | 最後にLLMから正常な回答が返された日時。`created_at`より過去にはできない |
| `version` | `int` | 必須 | 楽観排他に使用する更新バージョン。生成時は0で、会話記録時に1増加する |

#### 操作

| 操作 | 入力 | 結果 | 関連するDomainルール | 送出するDomainエラー |
| --- | --- | --- | --- | --- |
| `create` | `chat_id`, `session_id`, `title`, `user_id`, `answered_at` | `created_at`と`last_updated_at`に初回の正常回答日時`answered_at`を設定した`Chat`を生成する | DR-01, DR-06 | `InvalidChatIdError`, `InvalidSessionIdError` |
| `record_exchange` | ユーザーの`ChatMessage`、LLMの`ChatMessage` | 同じチャットターンに属することと継続会話の発信順序を検証し、`last_updated_at`をLLMメッセージの発信日時へ更新して`version`を1増加する | DR-02, DR-05, DR-07, DR-09 | `MessageSentAtOutOfOrderError`, `InvalidMessageSenderError`, `InvalidChatTurnError` |

### ChatMessage

- 種別: Value Object
- 識別子: なし。個々のメッセージを識別して更新・削除する要件はない
- 責務: チャット内で発信された1件の内容と、その発信者および発信日時を表現する

#### 属性

| 属性名 | 型 | 必須 | 説明・制約 |
| --- | --- | --- | --- |
| `chat_id` | UUID | 必須 | メッセージが属するチャットの識別子 |
| `request_id` | UUID v7 | 必須 | ユーザー質問と対応するLLM回答を関連付ける識別子 |
| `sender` | `MessageSender` | 必須 | ユーザーまたはLLM |
| `content` | `Prompt \| str` | 必須 | ユーザー発信の場合は`Prompt`。LLM発信の場合は文字数上限を設けない`str` |
| `sent_at` | タイムゾーンを含む日時 | 必須 | メッセージが発信された日時 |

#### 操作

| 操作 | 入力 | 結果 | 関連するDomainルール | 送出するDomainエラー |
| --- | --- | --- | --- | --- |
| 生成 | `chat_id`, `request_id`, `sender`, `content`, `sent_at` | `ChatMessage`を生成する | DR-01, DR-02 | `InvalidChatIdError`, `InvalidPromptError`, `PromptTooLongError`, `InvalidMessageSenderError`, `InvalidChatTurnError` |

## 6. Value Object

### Prompt

- 表現する値: LLMへ渡すユーザーのプロンプト
- 保持する値: `str`
- 等価性: 前後の空白文字を除去した後の文字列が同一である場合に等価
- 制約: 前後の一般的な空白文字を除去した後、空文字ではなく、文字数が1,000文字以下であること
- 振る舞い: 生成時に前後の一般的な空白文字を除去し、整形済みの値を提供する
- 違反時のDomainエラー: `InvalidPromptError`, `PromptTooLongError`

### MessageSender

- 表現する値: チャットメッセージの発信主体
- 保持する値: ユーザーまたはLLMを表す列挙値
- 等価性: 同じ発信主体である場合に等価
- 制約: ユーザーまたはLLMのいずれかであること
- 振る舞い: 該当なし。発信主体を型で制限する
- 違反時のDomainエラー: `InvalidMessageSenderError`

## 7. Domainルール

どのユースケースから呼ばれても常に成立する不変条件と状態遷移のみを記載する。ユースケース固有の条件はユースケース仕様書へ記載する。

### DR-01: チャット識別子とセッション識別子の有効性

- 対象: `Chat`
- 内容: `chat_id`はUUID v7であり、`session_id`は空文字および空白文字のみではない`str`でなければならない
- 違反時のDomainエラー: `InvalidChatIdError`, `InvalidSessionIdError`

### DR-02: チャットメッセージの構成

- 対象: `ChatMessage`
- 内容: チャットメッセージは、チャットID、チャットターンID、ユーザーまたはLLMの発信者、発信者に対応する内容、発信日時を必ず持つ。ユーザー発信の内容には`Prompt`を使用し、LLM発信の内容には1,000文字の上限を適用しない
- 違反時のDomainエラー: `InvalidPromptError`, `PromptTooLongError`, `InvalidMessageSenderError`, `InvalidChatTurnError`

### DR-03: プロンプトの整形

- 対象: `Prompt`
- 内容: プロンプトは生成時に前後の改行、タブ、半角スペース、全角スペースなどの一般的な空白文字を除去し、以降は整形済みの値を保持する
- 違反時のDomainエラー: 該当なし

### DR-04: プロンプトの有効性

- 対象: `Prompt`
- 内容: 整形後のプロンプトは空文字ではなく、文字数が1,000文字以下でなければならない
- 違反時のDomainエラー: `InvalidPromptError`, `PromptTooLongError`

### DR-05: チャットメッセージの発信順序

- 対象: `Chat`
- 内容: 継続会話を記録する場合、ユーザーメッセージの発信日時は現在の`last_updated_at`より過去であってはならず、LLMメッセージの発信日時はユーザーメッセージの発信日時より過去であってはならない。正常なLLMメッセージを記録した後、`last_updated_at`はLLMメッセージの発信日時と一致しなければならない
- 違反時のDomainエラー: `MessageSentAtOutOfOrderError`

### DR-06: チャット日時の初期状態

- 対象: `Chat`
- 内容: チャット生成時の`created_at`と`last_updated_at`は、初回の正常なLLM回答日時と一致しなければならない
- 違反時のDomainエラー: 該当なし。生成操作が同じ日時を設定する

### DR-07: チャットターンの構成

- 対象: ユーザーの`ChatMessage`、LLMの`ChatMessage`
- 内容: 1つのチャットターンは、同じ`chat_id`と`request_id`を持つユーザーメッセージ1件とLLMメッセージ1件で構成する
- 違反時のDomainエラー: `InvalidChatTurnError`

### DR-08: 初回チャットターンの発信順序

- 対象: 初回のユーザー`ChatMessage`、初回のLLM `ChatMessage`、`Chat`
- 内容: 初回ユーザーメッセージの発信日時は初回LLMメッセージの発信日時より後であってはならず、初回LLMメッセージの発信日時は`Chat.created_at`および`Chat.last_updated_at`と一致しなければならない
- 違反時のDomainエラー: `MessageSentAtOutOfOrderError`

### DR-09: チャット更新バージョン

- 対象: `Chat`
- 内容: チャット生成時の`version`は0とし、正常な会話を記録するたびに1増加する
- 違反時のDomainエラー: 該当なし。生成操作と会話記録操作が更新する

## 8. Domainエラー

| エラー | 発生条件 | 呼び出し側が区別する理由 |
| --- | --- | --- |
| `InvalidChatIdError` | `chat_id`がUUIDではない | 不正な識別子を持つチャットまたはメッセージの生成を拒否するため |
| `InvalidSessionIdError` | `session_id`が空文字または空白文字のみ | 外部会話を継続できないチャットの生成を拒否するため |
| `InvalidPromptError` | 整形後のプロンプトが空文字 | 入力内容の修正を要求するため |
| `PromptTooLongError` | 整形後のプロンプトが1,000文字を超える | 許容文字数内への修正を要求するため |
| `InvalidMessageSenderError` | 発信者がユーザーまたはLLM以外 | 不正な発信者を持つメッセージの生成を拒否するため |
| `InvalidChatTurnError` | 同一ターンにユーザー質問とLLM回答が1件ずつ存在しない、または`chat_id`・`request_id`が一致しない | 不完全または不整合な会話の保存を拒否するため |
| `MessageSentAtOutOfOrderError` | ユーザーメッセージが現在の最終更新日時より過去、またはLLMメッセージがユーザーメッセージより過去 | 発信日時の順序が不正な会話記録を拒否するため |

`DomainError`自体は直接送出しない。

## 9. Command Repository Protocol

Repository Protocolは、同一トランザクションで整合性を保証する保存単位に対応したポート契約を定義する。

| Protocol | 操作 | 引数 | 戻り値 | 送出するエラー |
| --- | --- | --- | --- | --- |
| `ChatCommandRepositoryProtocol` | `get_chat_for_continuation` | `chat_id`, `user_id` | 更新対象の`Chat` | `ChatNotFoundError`, `ChatLoadError` |
| `ChatCommandRepositoryProtocol` | `save_started_chat` | `Chat`, 同じ`request_id`を持つユーザー・LLMの`ChatMessage` | なし | `ChatSaveError` |
| `ChatCommandRepositoryProtocol` | `save_exchange` | 更新済み`Chat`, 同じ`request_id`を持つユーザー・LLMの`ChatMessage` | なし | `ChatSaveError`, `ChatConflictError` |
| `ChatTitleRepositoryProtocol` | `update_title` | `chat_id`, `user_id`, `title` | なし | `ChatNotFoundError`, `ChatTitleUpdateError` |
| `ChatDeletionRepositoryProtocol` | `delete_chat` | `chat_id`, `user_id` | なし | `ChatNotFoundError`, `ChatDeleteError` |

`save_exchange`は、永続化済みの更新バージョンが取得時点から変更されていない場合のみ、チャット本体更新と2メッセージ追加を同一トランザクションで行う。バージョンが一致しない場合は`ChatConflictError`を送出し、いずれも保存しない。

読み取り専用のQuery Repository ProtocolはApplication層に定義するため、本節には記載しない。

## 10. 関連するDomain Service

- 該当なし。メッセージの発信順序を保証するDomainオブジェクトの境界は未確定だが、現時点ではDomain Serviceの必要性も確定していない

## 11. テスト観点

- 正常系: UUID v7のチャットIDとリクエストID、有効なユーザーID、有効なセッションIDを持つチャットの生成、作成日時と最終更新日時の一致、同じリクエストIDを持つユーザー質問とLLM回答、有効なプロンプトの生成と整形、時系列に沿った会話記録
- 境界値: 整形後のプロンプトが空文字、1文字、999文字、1,000文字、1,001文字となる場合
- 異常系: 空文字または空白文字のみのセッションID、一般的な空白文字のみのプロンプト、1,000文字を超えるユーザープロンプト、不正な発信者、不正なリクエストID、質問と回答の`chat_id`・`request_id`不一致、最新メッセージより過去の発信日時
- トランザクション: 初回開始時は`Chat`本体と初回2メッセージ、会話継続時は`Chat.last_updated_at`・`version`更新と新規2メッセージが同時に保存されること
- 楽観排他: 同じ更新バージョンから開始した複数の会話継続では、最初の保存のみ成功し、競合した保存ではチャット本体とメッセージが変更されないこと

## 12. 関連仕様書

- ユースケース仕様書: `docs/backend/specification/usecases/chat/start_chat.md`
- ユースケース仕様書: `docs/backend/specification/usecases/chat/continue_chat.md`
- ユースケース仕様書: `docs/backend/specification/usecases/chat/rename_chat.md`
- ユースケース仕様書: `docs/backend/specification/usecases/chat/delete_chat.md`
- 外部接続仕様書: 該当なし。Domain層は外部接続へ依存しない

## 13. 未確定事項

- `title`の制約。現時点では検討対象外
- チャットIDの重複保存時に必要なRepository契約エラー
