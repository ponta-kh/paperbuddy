---
name: create-backend-domain-specification
description: バックエンドのドメインモデル仕様書またはDomain Service仕様書を、業務ルールとDomain層の規約に整合させて新規作成する。Entity、Value Object、Aggregate、不変条件、状態遷移、Domain例外、Command Repository Protocol、単一Domainオブジェクトへ自然に配置できない業務判断を実装前に明文化する場合に使用する。
---

# バックエンドドメイン仕様書作成

実装前に、ドメインモデルまたはDomain Serviceが保証する業務ルールを仕様書として作成する。

## 出力規則

- ドメインモデル仕様書は `docs/backend/specification/domain/[domain名]/domain.md` に作成する。
- Domain Service仕様書は `docs/backend/specification/domain/[domain名]/domain-services/[service名].md` に作成する。
- `[domain名]` は既存コード・仕様書の用語に合わせた英小文字のsnake_caseとする。
- `[service名]` はDomain Service名に合わせた英小文字のsnake_caseとする。
- 1つのドメインモデル仕様書には1つのドメインのみを記載する。
- 1つのDomain Service仕様書には1つのDomain Serviceのみを記載する。
- ドメインモデル仕様書は `assets/domain-specification-template.md` を使用する。
- Domain Service仕様書は `assets/domain-service-specification-template.md` を使用する。
- テンプレート項目は削除せず、該当しない場合は理由とともに「該当なし」と記載する。
- 未確定事項を推測で確定せず、`未確定事項`へ記載する。

## 必須の参照資料

- 作業開始時と最終確認前に `docs/backend/architecture.md` と `docs/backend/layer/domain.md` を読む。
- `docs/backend/specification/README.md` を読み、仕様書の配置規則に従う。
- 関連する責務を確認するため、`docs/backend/layer/application.md` と `docs/backend/layer/infrastructure.md` を読む。
- `docs/backend/naming-conventions.md` が存在する場合は読む。
- 同じドメインの既存ユースケース仕様書、コード、テストを調査し、用語と業務ルールを揃える。
- 関連する外部接続仕様書が存在する場合は参照する。ただし、外部接続の実装詳細をDomain仕様へ持ち込まない。

## 作業手順

### 1. 対象ドメインを特定する

1. 作成対象がドメインモデル仕様書かDomain Service仕様書かを特定する。
2. ドメインの目的、対象範囲、対象外を整理する。
3. 業務用語と概念を特定する。
4. 関連する既存仕様、コード、テストを調査する。
5. 情報不足や矛盾を未確定事項として整理する。

### 2. Domainモデルを整理する

ドメインモデル仕様書を作成する場合は、以下を整理する。

- Entityと識別子。
- Value Objectと制約。
- Aggregate Rootと境界。境界を確定できない場合は未確定とする。
- 不変条件と状態遷移。
- ユースケース仕様書から参照するドメインルール識別子`DR-XX`。
- Domain Serviceが必要な業務ルール。
- 呼び出し側の対応を分ける必要があるDomain例外。
- Aggregate Root単位のCommand Repository Protocol。

Domain Service仕様書を作成する場合は、以下を整理する。

- 単一のEntityまたはValue Objectへ自然に配置できない理由。
- 関係するDomainオブジェクト。
- 状態を持たずに行う業務判断。
- 入力、出力、Domainルール、Domain例外。
- 関連するドメインモデル仕様書。

Domain層で扱うべき業務ルールと、Application層で扱うユースケース固有の判断を混同しない。

### 3. 仕様書を作成する

1. 対象に対応するテンプレートを基に仕様書を作成する。
2. 業務上の意味と制約を中心に記述する。
3. HTTP、DB、ORM、SDKなどの実装詳細を記載しない。
4. 各ルールについて、違反時に発生するDomain例外を明確にする。
5. ユースケース仕様書から参照するドメインルールには、ドメインモデル仕様書とDomain Service仕様書を通してドメイン内で一意かつ安定した`DR-XX`を割り当てる。
6. Domain ServiceにはRepository、外部API、外部サービスなどの外部依存を持たせない。
7. 関連するユースケース仕様書や外部接続仕様書が不足している場合は指摘するが、明示的な依頼なしに作成しない。

### 4. 最終確認する

1. Domain層規約、Architecture、関連仕様書を読み直す。
2. 対象がドメインモデルの場合は、Entity、Value Object、Aggregate、不変条件、状態遷移、例外の間に矛盾がないことを確認する。
3. 対象がDomain Serviceの場合は、状態や外部依存を持たず、ユースケースの処理手順になっていないことを確認する。
4. 同値分割と境界値分析に必要な条件が読み取れることを確認する。
5. 作成ファイル、確定事項、未確定事項、関連仕様書の不足を報告する。

## 制約

- ユーザー要求や既存資料にない業務ルールを無断で追加しない。
- Domain層へユースケースの処理手順や外部システムの都合を持ち込まない。
- Aggregate境界を根拠なく確定しない。
- Domain Serviceを、Application層のユースケースや外部接続処理の代替として作成しない。
- 既存仕様書を明示的な依頼なしに変更しない。
