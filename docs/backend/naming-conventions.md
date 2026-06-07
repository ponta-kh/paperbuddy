# バックエンド命名規約

バックエンド全体で共通して適用する命名規約を定義する。

レイヤーや構成要素の責務に固有の命名規約は、各レイヤーのドキュメントで定義する。

## Pythonの命名形式
- クラス名は`PascalCase`とする
- 関数名、メソッド名、変数名、引数名、モジュール名、パッケージ名は`snake_case`とする
- 定数名は`UPPER_SNAKE_CASE`とする
- 非公開の名前は先頭にアンダースコアを付ける

## 命名原則
- プロジェクト内で定義されたドメイン用語を使用する
- 同じ概念に複数の異なる名前を使用しない
- 名前から役割や対象を判断できる具体的な名前を使用する
- 意味が曖昧な省略語や、プロジェクト内で定義されていない略語を使用しない
- 実装技術ではなく、責務や業務上の意味を表す名前を優先する

## 共通サフィックス
- 例外クラスは`Error`で終える
- Protocolは`Protocol`で終える

## レイヤー固有の命名規約
- [Application層](layer/application.md)
- [Domain層](layer/domain.md)
- [Infrastructure層](layer/infrastructure.md)
- [Presentation層](layer/presentation.md)
- [dependencies層](layer/dependencies.md)
