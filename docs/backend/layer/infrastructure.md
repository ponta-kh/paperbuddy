# infrastructure 層

## 責務
Repository、外部APIクライアント、SDKクライアントなど、外部システムへ接続する具体的な実装を提供する。

- Application層またはDomain層で定義された出力ポートを実装する
- DB、外部API、LLM、ストレージなどの実装詳細を内側の層から隠す
- 外部システム固有の形式と、Application層またはDomain層で定義された型を相互変換する
- 実装固有の例外を、出力ポートの契約で定義された例外へ変換する

業務ロジックやユースケース上の判断は行わない。

## 依存可能なレイヤー
- Application層
- Domain層
- 外部システムへ接続するためのSDK、ORM、DBドライバー

Presentation層には依存しない。

## Repository
- Application層またはDomain層で定義されたRepository Protocolを実装する
- Query Repository ProtocolとCommand Repository Protocolを、同一のRepositoryクラスで実装してよい
- ORMモデルやDBドライバー固有の型をInfrastructure層の外へ返さない
- Domain Entityとの相互変換はRepository内で行う
- Query用途では、出力ポートの契約で定義された読み取り専用モデルを返してよい
- ORMモデル、Domain Entity、読み取り専用モデル間の変換はRepository内で直接行う
- Repository内で業務判断を行わない
- Repository内でトランザクションを独自に開始、コミット、ロールバックしない

変換処理を分離する専用Mapperは設けない。変換処理が複雑になり、Repositoryの責務が不明確になった場合に分離を検討する。

### 該当データが存在しない場合
単一の対象を取得するRepository操作で該当データが存在しない場合は、`None`などの正常値を返さず、共通の`RepositoryNotFoundError`を送出する。

`RepositoryNotFoundError`は、出力ポートの契約としてApplication層に定義する。Infrastructure層に独自のNot Found例外や対象ごとのNot Found例外は定義しない。

該当データが存在しないことをエラーとして扱うか、正常系の結果として扱うかはApplication層が判断する。正常系として扱うユースケースは`RepositoryNotFoundError`を捕捉し、適切な出力へ変換する。

複数件を取得する操作で該当データが0件の場合も、同様に`RepositoryNotFoundError`を送出する。これにより、Repositoryごとに空のコレクションと例外が混在することを防ぐ。

## 外部API・LLM・ストレージ
- SDKのRequest型、Response型、例外などの実装固有型をInfrastructure層の外へ漏らさない
- 出力ポートの契約で定義された入力型と出力型へ変換する
- APIキー、接続先、タイムアウトなどの設定値は外部から受け取る
- 外部通信にはタイムアウトを設定する
- 業務上の代替処理やフォールバックは行わず、Application層の判断に委ねる

自動リトライに関する規約は、必要になった時点で定義する。それまではInfrastructure層で自動リトライを行わない。

## 外部クライアントの生成
DB接続、HTTPクライアント、SDKクライアントなどは、Infrastructure層の実装内で生成せず、Dependencies層から注入する。

クライアントの共有範囲、生成タイミング、破棄タイミングなどのライフサイクルは、Dependencies層で管理する。

## 設定・機密情報
- APIキー、DB接続情報、AWS認証情報などをコードへ直接記述しない
- 機密情報は環境変数またはSecrets Managerから取得する
- 設定値や外部クライアントは、Dependencies層から注入する
- Infrastructure層の実装から環境変数などをグローバルに直接参照しない
- 機密情報を例外へ含めない

## エラーハンドリング
Infrastructure層は、SDK、DBドライバー、外部APIクライアントなどの実装固有例外を上位層へ漏らさない。

実装固有例外は、出力ポートの契約としてApplication層またはDomain層で定義された例外へ変換する。例外を変換する際は、原因を追跡できるように`raise ... from error`で元の例外を例外チェーンへ保持する。

想定可能な失敗は、呼び出し側が後続処理を判断できる具体的な例外へ変換する。想定外の接続障害やサービス障害についても、出力ポートで定義された抽象化された技術例外へ変換する。

ただし、`Exception`を一律に捕捉してすべて同じ例外へ変換してはならない。プログラムの不具合など、変換対象として定義されていない例外は握り潰さない。

具体的な例外分類と変換ルールは、Repository、外部API、その他の接続先ごとに今後定義する。

## テスト方針
- 出力ポートで定義された引数、戻り値、例外の契約を満たすことをテストする
- ORMモデルやSDK固有型がInfrastructure層の外へ漏れないことをテストする
- 実装固有例外が、出力ポートで定義された例外へ正しく変換されることをテストする
- 該当データが存在しない場合に、`RepositoryNotFoundError`が送出されることをテストする
- 外部API、LLM、ストレージのSDK呼び出しはモックまたはスタブに差し替える
- Repositoryは、利用するDBとの統合テストを用意する
- LLM出力はスキーマと必要なキーワードを検証する
