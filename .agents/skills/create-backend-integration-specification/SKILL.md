---
name: create-backend-integration-specification
description: バックエンドの外部接続仕様書を、Infrastructure層と出力ポートの契約に整合させて docs/backend/specification/infrastructure/[integration名].md へ新規作成する。外部API、LLM、ストレージ、SDK、DBなどの接続方式、入出力変換、例外変換、設定、制約を実装前に明文化する場合に使用する。
---

# バックエンド外部接続仕様書作成

実装前に、1つの外部接続先またはInfrastructureアダプターの契約と制約を明文化する。

## 出力規則

- `docs/backend/specification/infrastructure/[integration名].md` に作成する。
- `[integration名]` は既存コード・仕様書の用語に合わせた英小文字のsnake_caseとする。
- 1つの仕様書には1つの外部接続先またはInfrastructureアダプターのみを記載する。
- `assets/integration-specification-template.md` を必ずベースとして使用する。
- テンプレート項目は削除せず、該当しない場合は理由とともに「該当なし」と記載する。
- 未確定事項を推測で確定せず、`未確定事項`へ記載する。

## 必須の参照資料

- 作業開始時と最終確認前に `docs/backend/architecture.md` と `docs/backend/layer/infrastructure.md` を読む。
- `docs/backend/specification/README.md` を読み、仕様書の配置規則に従う。
- 出力ポートと依存関係を確認するため、`docs/backend/layer/application.md`、`docs/backend/layer/domain.md`、`docs/backend/layer/dependencies.md` を読む。
- `docs/backend/naming-conventions.md` が存在する場合は読む。
- 関連するユースケース仕様書、ドメイン仕様書、既存コード、テストを調査する。
- 接続先の仕様確認が必要な場合は、公式ドキュメントなど一次情報を使用する。

## 作業手順

### 1. 接続対象を特定する

1. 接続先、利用目的、対象操作、対象外を整理する。
2. 関連する出力ポートと利用ユースケースを特定する。
3. 認証方式、設定値、制約、障害条件を調査する。
4. 情報不足や矛盾を未確定事項として整理する。

### 2. 接続契約を整理する

- 出力ポートの操作とInfrastructure実装の対応。
- 内部型と外部固有形式の入出力変換。
- タイムアウト、リトライ、レート制限、容量などの制約。
- SDK・外部サービス固有例外から契約上の例外への変換。
- 必要な設定値と機密情報。
- クライアントの生成・破棄・共有範囲。

業務上の代替処理やフォールバックは定義せず、Application層の仕様へ委ねる。

### 3. 仕様書を作成する

1. テンプレートを基に仕様書を作成する。
2. 出力ポートから観測できる契約とInfrastructure固有の制約を記述する。
3. APIキーや認証情報の実値を記載しない。
4. 自動リトライは既存規約または明示的要求がある場合のみ記載する。
5. 関連するユースケース仕様書やドメイン仕様書が不足している場合は指摘するが、明示的な依頼なしに作成しない。

### 4. 最終確認する

1. Infrastructure層規約、Architecture、関連仕様書を読み直す。
2. SDK・ORM・DBドライバー固有型や例外が内側へ漏れていないことを確認する。
3. 入出力変換、例外変換、設定、タイムアウト、ライフサイクルの間に矛盾がないことを確認する。
4. 作成ファイル、確定事項、未確定事項、関連仕様書の不足を報告する。

## 制約

- ユーザー要求や一次情報にない接続仕様を無断で追加しない。
- 業務ロジックやユースケースの代替処理をInfrastructure仕様へ持ち込まない。
- 機密情報を仕様書へ記載しない。
- 既存仕様書を明示的な依頼なしに変更しない。
