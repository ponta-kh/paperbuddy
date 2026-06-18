# 基本ルール
常に日本語で回答してください
コメントやdescriptionなども常に日本語で記入するようにしてください

# コマンド規約
- Pythonパッケージ管理: `uv add` / `uv run` / `uv sync`（pip使用禁止）
- Node.jsパッケージ管理: `pnpm add` / `pnpm install`（npm・yarn使用禁止）

# テスト方針
- テスト設計は同値分割・境界値分析を基本とする
- LLMの出力テストはスキーマ検証・キーワード検証で行う
- LLM呼び出しはモック/スタブに差し替えてユニットテストを書く

# フロントエンド画面構成
- PageはContainerを組み立てる責務に限定する
- Containerは状態管理・データ変換・副作用・イベント処理を担当し、Componentを組み立てる
- Componentはpropsに基づいて表示する純粋関数とし、状態管理・データ取得・副作用を持たせない
- Container専用のComponentは `components/[Container名]/` 配下にまとめる
- `View`という命名のComponentは作成しない

# 注意事項
- APIキー・AWSクレデンシャルはコードに直書きしない（環境変数・Secrets Manager）
- ALBはプライベートサブネットに配置する（パブリック公開禁止）
- CloudFrontをすべてのトラフィックの唯一の入口とする
