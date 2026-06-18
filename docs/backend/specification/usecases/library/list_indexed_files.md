# ListIndexedFiles ユースケース仕様書

## 1. 概要

- ドメイン: `library`
- 分類: `Query`
- 目的: RAGへ取り込み済みのデータソース一覧を取得する
- アクター: 認証済みユーザー

## 2. 対象範囲

### 対象

- データソース一覧の取得
- 分類とファイル名の昇順での並び替え
- 取得結果が0件の場合の空一覧返却

### 対象外

- データソースの登録、更新、削除
- S3オブジェクトの実体操作
- 分類の再計算やステータス更新

## 3. 前提条件・事後条件

### 前提条件

- ユーザーが認証済みである
- データソース情報が保存されている

### 正常終了時の事後条件

- データソースが分類、ファイル名の昇順で返される
- 0件の場合は空の一覧が返される

### 異常終了時の事後条件

- 業務上の状態は変更されない

## 4. 入力

- 入力型: `ListIndexedFilesInput`
- 引数名: `query`

| フィールド名 | 型・形式 | 必須 | 制約・説明 |
| --- | --- | --- | --- |
| `request_id` | UUID v7 | 必須 | Presentationで採番されたリクエスト識別子。将来のログ出力で処理を関連付けるために使用する |

## 5. 出力

- 出力型: `ListIndexedFilesOutput`

| フィールド名 | 型・形式 | 説明 |
| --- | --- | --- |
| `files` | `tuple[IndexedFileOutput, ...]` | 分類、ファイル名の昇順に並んだデータソース一覧 |
| `IndexedFileOutput.source_id` | UUID | データソース識別子 |
| `IndexedFileOutput.s3_key` | `str` | S3オブジェクトキー |
| `IndexedFileOutput.name` | `str` | ファイル名 |
| `IndexedFileOutput.category` | `str` | 書類分類 |
| `IndexedFileOutput.status` | `str` | 取り込みステータス |
| `IndexedFileOutput.s3_uploaded_at` | タイムゾーンを含む日時 | S3アップロード日時 |
| `IndexedFileOutput.rag_indexed_at` | タイムゾーンを含む日時または`null` | RAG組み込み日時 |

## 6. 認可要件

- 認証済みユーザーのみ実行できる
- 現時点では所有者による絞り込みは行わない

## 7. トランザクション・整合性

- トランザクション境界: 1ユースケース
- 更新対象Aggregate: 該当なし。Queryのため状態を変更しない
- 保証する整合性: データソース一覧は分類、ファイル名の昇順で返される

## 8. 使用するポート

| Protocol | 操作 | 用途 | 送出する可能性のあるエラー |
| --- | --- | --- | --- |
| `IndexedFileQueryRepositoryProtocol` | `list_indexed_files` | データソース一覧を取得する | `RepositoryNotFoundError`, `RepositoryAccessError` |

## 9. 基本フロー

1. データソース一覧を取得する。
2. 分類、ファイル名の昇順に並び替える。
3. 出力モデルへ変換して返す。

## 10. 代替フロー

### 対象データが存在しない

- 発生条件: `RepositoryNotFoundError`が送出される
- 振る舞い: 空の一覧へ変換する
- 結果: 正常終了し、空の一覧を返す

## 11. 異常系

| 例外 | 発生条件 | 呼び出し元への結果 |
| --- | --- | --- |
| `RepositoryAccessError` | データソース一覧の取得に失敗する | 例外を送出する |

## 12. 受け入れ条件

- 取得結果は分類、ファイル名の昇順で返される
- 0件の場合は空の一覧が返される
- 返却項目はID、S3 Key、ファイル名、分類、ステータス、S3アップロード日時、RAG組み込み日時である
