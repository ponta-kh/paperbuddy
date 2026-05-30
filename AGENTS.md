# コマンド規約
- Pythonパッケージ管理: `uv add` / `uv run` / `uv sync`（pip使用禁止）
- Node.jsパッケージ管理: `pnpm add` / `pnpm install`（npm・yarn使用禁止）

# テスト方針
- テスト設計は同値分割・境界値分析を基本とする
- LLMの出力テストはスキーマ検証・キーワード検証で行う
- LLM呼び出しはモック/スタブに差し替えてユニットテストを書く

# 注意事項
- APIキー・AWSクレデンシャルはコードに直書きしない（環境変数・Secrets Manager）
- ALBはプライベートサブネットに配置する（パブリック公開禁止）
- CloudFrontをすべてのトラフィックの唯一の入口とする