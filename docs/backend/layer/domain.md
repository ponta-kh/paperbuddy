# Domain 層

## 責務
Domain層は、業務上の概念、業務ルール、不変条件を表現する。

- 業務上の概念をEntityやValue Objectとして表現する
- 業務ルールをEntity、Value Object、Domain Serviceとして実装する
- 不正な状態の生成および保持を防ぐ
- 業務ルール違反をDomain例外として表現する
- Domain Entityを永続化するためのCommand Repository Protocolを定義する

HTTP、DB、外部API、フレームワークなどの実装都合を持ち込まない。

## 依存可能なもの
- Domain層内の他の構成要素
- 標準ライブラリ

Application層、Infrastructure層、Presentation層、および外部ライブラリには依存しない。

## 配置するもの
- Entity
- Value Object
- Domain Service
- Domain例外
- Command Repository Protocol

## 配置しないもの
- ユースケースの処理手順
- HTTPステータスコードやレスポンス形式
- PydanticモデルやORMモデル
- DB、外部API、LLM、ストレージなどへの接続処理
- ログ、メトリクス、トレースなどの運用処理

## Entity
Entityは、識別子によって同一性を判断する業務上の概念を表現する。

- 状態変更はEntity自身のメソッドを通して行う
- 業務ルールを回避できる汎用的なsetterを提供しない
- 生成時および状態変更後に不変条件を満たすことを保証する
- 業務ルールに違反する操作はDomain例外を送出する
- ORMモデルとして直接使用しない
- Entity同士の同一性は識別子で判断する

Entityを可変にするか不変にするかは、そのEntityの状態遷移を自然に表現できる方を選択する。どちらの場合も、外部から不正な状態へ変更できないようにする。

### 生成
Entityを生成するための不変条件が単純な場合は、コンストラクタまたはクラスメソッドで生成する。

生成処理が複雑になった場合や、生成方法が複数存在する場合に限りFactoryへの分離を検討する。

Entityの識別子をApplication層、Domain層、Infrastructure層のどこで生成するかは、識別子の性質とユースケースに応じて決定する。Domain層で生成する場合も、DBや外部サービス固有の仕組みには依存しない。

## Value Object
Value Objectは、識別子を持たず、値によって等価性を判断する業務上の概念を表現する。

- 原則として不変にする
- 生成時に自身の不変条件を検証する
- 不正な値では生成できないようにする
- 等価性は保持する値によって判断する
- 値に関する業務ルールや振る舞いを自身に持たせる

業務上の意味、制約、または振る舞いを持つ値をValue Objectとする。単なるデータ保持のために、すべてのプリミティブ値をValue Objectへ変換してはならない。

Value Objectからプリミティブ値を取得する必要がある場合は、そのための明示的なプロパティまたはメソッドを提供する。

## Domain Service
Domain Serviceは、単一のEntityまたはValue Objectへ自然に配置できない業務ルールを表現する。

- 状態を持たない
- 複数のDomainオブジェクトに関係する業務判断のみを行う
- Repositoryや外部APIなどの外部システムを直接呼び出さない
- ユースケースの処理手順を記述しない

Domain Serviceを安易に作成せず、業務ルールをEntityやValue Objectへ配置できない場合に限り使用する。

## Aggregate
個別のAggregate境界は、各機能またはドメインの設計時に決定する。すべてのドメインへ共通する境界は定義しない。

Aggregateを設計する場合は、以下を原則とする。

- Aggregateは、同一トランザクション内で整合性を保証する必要があるDomainオブジェクトの単位とする
- Aggregateごとに、外部から操作する入口となるAggregate Rootを1つ定める
- Aggregate内部のEntityは、Aggregate Rootを経由して操作する
- Aggregate内部の不変条件は、Aggregate Rootが保証する
- Repositoryは原則としてAggregate Root単位で定義する
- 1つのトランザクションで変更するAggregateは、原則として1つとする
- 複数のAggregateにまたがる処理は、Application層で調整する

同一トランザクションでの即時整合性が必要か、独立したライフサイクルを持つか、一緒に読み書きした場合のサイズや性能に問題がないかを考慮して、Aggregate境界を判断する。

## Command Repository Protocol
Domain Entityの永続化に関するCommand Repository Protocolは、Domain層に定義する。

- 原則としてAggregate Rootの保存、更新、削除に必要な操作を定義する
- 汎用的なCRUD操作ではなく、Domain層が必要とする操作のみを定義する
- 引数および戻り値にORMモデルやDBドライバー固有型を使用しない
- 読み取り専用のQuery Repository ProtocolはApplication層に定義する
- Infrastructure層の具体的なRepository実装には依存しない

## エラーハンドリング
Domain例外は、業務ルール違反を表す。

- すべてのDomain例外が継承する共通基底例外`DomainError`を定義する
- 呼び出し側の対応を分ける必要がある業務上の失敗理由ごとに、`DomainError`を継承した具体的な例外を定義する
- `DomainError`自体は直接送出せず、具体的な派生例外を送出する
- 同じ対応でよく、呼び出し側が区別する必要がない複数のチェックでは、同じ具体的な例外を使用してよい
- `ValueError`や`RuntimeError`などの汎用例外を業務エラーとして使用しない
- HTTPステータスコード、エラーコード、利用者向けメッセージなど、外部公開形式を持たせない
- SDK、ORM、DBなどの実装固有情報を持たせない
- 予期しないプログラムエラーをDomain例外へ変換しない

Domain例外はDomain層内で不要に捕捉せず、呼び出し元へ送出する。

```python
class DomainError(Exception):
    pass


class ChatAlreadyClosedError(DomainError):
    pass
```

## テスト方針
- Domain層のテストは、外部システムに依存しない単体テストとする
- EntityとValue Objectの生成条件および不変条件をテストする
- Entityの正常な状態遷移と禁止された状態遷移をテストする
- Domain例外が正しい条件で送出されることをテストする
- 入力値のテストケースは、同値分割と境界値分析に基づいて設計する
- Domain Serviceの業務判断をテストする
- 外部依存を持たないため、モックやスタブは原則として使用しない
