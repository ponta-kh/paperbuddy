# [Domain Service名] Domain Service仕様書

## 1. 概要

- 所属ドメイン: `[domain名]`
- 目的: [このDomain Serviceが表現する業務判断]
- Domain Serviceとする理由: [単一のEntityまたはValue Objectへ自然に配置できない理由]

## 2. 対象範囲

### 対象

- [このDomain Serviceが担当する業務判断]

### 対象外

- [ユースケースの処理手順、外部接続など担当しない内容]

## 3. 責務

- [状態を持たずに行う業務判断]

## 4. 関係するDomainオブジェクト

| Domainオブジェクト | 種別 | 用途 |
| --- | --- | --- |
| [名前] | [Entity / Value Object / Aggregate Root] | [判断での利用目的] |

Repository、外部API、外部サービスなどの外部依存は記載しない。外部情報が必要な場合は、Application層が取得したDomainオブジェクトまたは値を入力として渡す。

## 5. 提供する操作

### [操作名]

- 説明: [業務判断の目的]
- 入力: [DomainオブジェクトまたはDomain型]
- 出力: [Domainオブジェクト、Value Object、または判断結果]
- 関連するDomainルール: [DR-XX]
- 送出するDomain例外: [具体的なDomainErrorの派生例外]

Domain Serviceは状態を保持せず、ユースケースの処理順序やRepository呼び出しを含めない。

## 6. Domain Serviceルール

Domain Service内で保証するルールにも`DR-XX`を割り当てる。ルールIDは、同じドメインのドメインモデル仕様書および他のDomain Service仕様書と重複させない。

### DR-XX: [ルール名]

- 内容: [複数のDomainオブジェクトに関係する業務ルール]
- 違反時のDomain例外: [具体的なDomainErrorの派生例外]

## 7. Domain例外

| 例外 | 発生条件 | 呼び出し側が区別する理由 |
| --- | --- | --- |
| [DomainErrorの派生例外] | [業務ルール違反] | [必要な対応差] |

`DomainError`自体は直接送出しない。

## 8. テスト観点

- 正常系: [代表的なDomainオブジェクトの組み合わせ]
- 境界値: [ルールの直前・境界・直後]
- 異常系: [Domain例外が発生する条件]
- 独立性: [外部依存や状態を持たずにテストできること]

## 9. 関連仕様書

- ドメインモデル仕様書: [パス]
- ユースケース仕様書: [パス。存在しない場合は不足を記載]

## 10. 未確定事項

- [確認が必要な事項。ない場合は「なし」]
