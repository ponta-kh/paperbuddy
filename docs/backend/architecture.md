# バックエンドのアーキテクチャ概要

## 選定アーキテクチャ
クリーンアーキテクチャを採用する

## フォルダ構成
```src/
├── domain/
│   ├── entities/
│   │   └── [domain]/
│   │       └── [domain].py
│   ├── value_objects/
│   │   └── [domain]/
│   │       └── [domain]_id.py
│   ├── exceptions/
│   │   └── [domain]_exception.py
│   └── repositories/
│       └── [domain]_command_repository_protocol.py # Commandリポジトリ
│
├── application/
│   ├── ports/
│   │   ├── input/
│   │   │   └── [domain]/
│   │   │       └── [use_case]_protocol.py                  # 入力ポート
│   │   └── out/
│   │       ├── [domain]/
│   │       │   └── [domain]_query_repository_protocol.py   # Queryリポジトリ
│   │       └── shared/
│   │           ├── llm_client_protocol.py                  # 例1:LLM呼び出し
│   │           └── file_upload_protocol.py                 # 例2:ファイルアップロード
│   └── use_cases/
│       └── [domain]/
│           └── [use_case]/
│               ├── [use_case].py
│               └── [use_case]_dto.py
│
├── infrastructure/
│   ├── repositories/
│   │   └── [domain]/
│   │       └── [domain]_repository.py  # Query・Commandリポジトリ 実装。必要に応じて分割する
│   ├── llm/
│   │   ├── gemini_client.py
│   │   └── claude_client.py
│   └── upload/
│       └── s3.py
│
├── presentation/
│   ├── routers/
│   │   └── [domain]_router.py
│   └── schemas/
│       └── [domain]_schema.py
│
├── dependencies/
│   └── [domain]_deps.py
│
└── shared/
    └── exceptions/
        └── base_exception.py
```
