# バックエンド仕様書の配置規則

`docs/backend/specification/` 配下の仕様書は、責務ごとに次の3フォルダへ配置する。

| フォルダ | 配置する仕様書 | 配置規則 |
|---|---|---|
| `domain/` | ドメインモデル、Domain Service | 直下をドメイン分類ごとのフォルダに分ける |
| `usecases/` | ユースケース | 直下をドメイン分類ごとのフォルダに分ける |
| `infrastructure/` | 外部接続先、Infrastructureアダプター | 仕様書を直下へ配置する |

## パス形式

- ドメインモデル: `docs/backend/specification/domain/[domain名]/domain.md`
- Domain Service: `docs/backend/specification/domain/[domain名]/domain-services/[service名].md`
- ユースケース: `docs/backend/specification/usecases/[domain名]/[use_case名].md`
- Infrastructure: `docs/backend/specification/infrastructure/[integration名].md`

`[domain名]`、`[service名]`、`[use_case名]`、`[integration名]` は、既存コードおよびドキュメントの用語に合わせた英小文字のsnake_caseとする。

## 仕様書に記載する設計契約

Protocolはクリーンアーキテクチャにおけるポート契約を表すため、特定のプログラミング言語やInfrastructure実装に依存しない仕様として記載する。

エラー名はユースケース、ドメイン、ポートが外部へ示す失敗理由の契約を表すため、プログラミング言語に依存しない仕様として記載する。

一方で、SDK、DB、フレームワーク、バッチサイズ、リトライ方法など、仕様フローそのものを左右しない実装上の工夫は仕様書へ記載せず、該当コードへコメントとして残す。
