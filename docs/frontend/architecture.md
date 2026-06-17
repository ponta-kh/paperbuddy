# フロントエンド構成

## レイヤー責務

- Page: Containerを配置するだけ。状態、API、データ変換ロジックを持たない。
- Container: データ取得、状態管理、データ変換、副作用、イベント処理を担当する。
- Section: Containerから受け取ったpropsで、複数Componentを意味のある表示単位に組み立てる。データ取得は禁止する。
- Component: 単一の表示部品。propsに基づく描画に徹し、データ取得は行わない。

## Section規約

- Containerが1つのSectionを返すだけの構造は禁止する。
- Sectionは業務状態、非同期処理、API呼び出しを持たない。
- Sectionは必須ではない。
- Sectionは`sections/[配置されるContainer名]/XXXSection.tsx`に配置する。
- Sectionは原則として配置先Container専用とする。複数Containerで再利用したくなった場合はComponent化を検討する。
- 永続性や外部影響のない純粋なUI状態はSectionまたはComponent内でも許容する。
- APIレスポンスから画面モデルへの変換、ソート、フィルタ、業務意味を持つ状態計算はContainerで行う。
