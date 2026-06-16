from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from boto3.dynamodb.types import TypeSerializer

_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
_JST = ZoneInfo("Asia/Tokyo")
_serializer = TypeSerializer()


@dataclass(frozen=True, slots=True)
class _SeedConversation:
    title: str
    first_question: str
    first_answer: str
    follow_up_question: str
    follow_up_answer: str


_CONVERSATIONS = (
    _SeedConversation(
        "Transformerの最新動向",
        "最近のTransformer研究で注目されている改善点を整理してください。",
        "近年は長文コンテキストの効率化、推論時の計算量削減、マルチモーダル統合が主要な研究テーマです。",
        "実運用で特に重要な観点は何ですか？",
        "精度だけでなく、推論レイテンシ、メモリ使用量、評価データの偏りを合わせて確認することが重要です。",
    ),
    _SeedConversation(
        "論文サーベイの進め方",
        "新しい研究分野の論文サーベイを効率よく進める方法を教えてください。",
        "代表的なサーベイ論文から用語と主要課題を把握し、引用関係をたどって重要論文を整理すると効率的です。",
        "論文を比較するときの軸も教えてください。",
        "目的、データセット、評価指標、ベースライン、計算コスト、制約事項を共通の表にまとめると比較しやすくなります。",
    ),
    _SeedConversation(
        "RAG評価指標の比較",
        "RAGシステムの評価指標にはどのようなものがありますか？",
        "検索精度、回答の忠実性、回答関連性、引用の正確性を分けて評価する方法が一般的です。",
        "オフライン評価だけで十分ですか？",
        "オフライン評価に加えて、実ユーザーの完了率や再質問率を継続的に観測することが望ましいです。",
    ),
    _SeedConversation(
        "埋め込みモデル選定",
        "日本語論文検索向けの埋め込みモデル選定基準を整理してください。",
        "日本語性能、専門用語への対応、ベクトル次元、推論速度、利用条件を基準に候補を比較します。",
        "検証データはどう作るべきですか？",
        "実際の検索質問と関連論文の組を用意し、難易度や分野が偏らないように分割して評価します。",
    ),
    _SeedConversation(
        "研究結果の再現性",
        "機械学習論文の再現性を確認するときのチェック項目を教えてください。",
        "データ前処理、乱数シード、ハイパーパラメータ、学習環境、評価手順が明記されているか確認します。",
        "コードが公開されていない場合はどうしますか？",
        "不足情報を仮定として明記し、複数条件で結果の頑健性を確かめることが重要です。",
    ),
    _SeedConversation(
        "長文要約手法",
        "長い論文を要約する代表的な手法を比較してください。",
        "全文を一度に処理する方法、章ごとに要約して統合する方法、検索で重要箇所を選んで要約する方法があります。",
        "情報の欠落を減らすにはどうすればよいですか？",
        "要約前に論文の目的、手法、結果、制約の抽出項目を定義し、最終結果に含まれるか検証します。",
    ),
    _SeedConversation(
        "引用ネットワーク分析",
        "引用ネットワークから研究分野の流れを把握する方法を教えてください。",
        "被引用数だけでなく、コミュニティ検出や時系列変化を用いることで主要テーマと分岐を把握できます。",
        "注意すべき偏りはありますか？",
        "古い論文や著名な研究者に引用が集中しやすいため、出版年や分野規模を考慮する必要があります。",
    ),
    _SeedConversation(
        "実験設計のレビュー",
        "提案手法の有効性を示す実験設計をレビューしてください。",
        "適切なベースライン、アブレーション、複数データセット、統計的なばらつきの報告が必要です。",
        "最低限必要なアブレーションは何ですか？",
        "提案手法の主要構成要素を個別に除外し、性能差と計算コストへの影響を確認します。",
    ),
    _SeedConversation(
        "論文の制約整理",
        "論文に書かれている制約事項を漏れなく整理する方法はありますか？",
        "Limitations、Discussion、実験条件を確認し、データ、手法、評価、運用の観点で分類します。",
        "明記されていない制約はどう扱いますか？",
        "実験対象外の条件や前提から推測し、推測であることを明示して追加検証項目にします。",
    ),
    _SeedConversation(
        "マルチモーダル研究比較",
        "画像と言語を扱う研究を比較するときの観点を教えてください。",
        "入力形式、融合方法、事前学習データ、評価タスク、モダリティ欠損時の頑健性を比較します。",
        "データセット依存を確認する方法はありますか？",
        "異なる収集条件のデータセットで評価し、ドメイン移行時の性能低下を測定します。",
    ),
    _SeedConversation(
        "推論コストの見積もり",
        "LLMを利用する研究の推論コストを比較したいです。",
        "入力・出力トークン数、呼び出し回数、モデル単価、レイテンシ、並列実行数を記録して比較します。",
        "精度とのトレードオフはどう表現しますか？",
        "精度と1件当たりコストを同じ図に配置し、要件を満たすパレート効率の良い構成を選びます。",
    ),
)


def seed_local_chats(
    client: Any,
    *,
    table_name: str,
    now: datetime | None = None,
) -> None:
    items = build_seed_items(now=now)
    for partition_key in dict.fromkeys(item["pk"] for item in items):
        _delete_partition(client, table_name=table_name, partition_key=partition_key)
    for item in items:
        client.put_item(TableName=table_name, Item=_serialize(item))


def build_seed_items(*, now: datetime | None = None) -> tuple[dict[str, Any], ...]:
    current = (now or datetime.now(timezone.utc)).astimezone(_JST)
    start_of_today = datetime.combine(current.date(), time.min, tzinfo=_JST)
    updated_at_values = (
        current - timedelta(minutes=1),
        current - timedelta(minutes=2),
        start_of_today - timedelta(days=1) + timedelta(hours=18),
        start_of_today - timedelta(days=3) + timedelta(hours=14),
        start_of_today - timedelta(days=6) + timedelta(hours=10),
        start_of_today - timedelta(days=8) + timedelta(hours=16),
        start_of_today - timedelta(days=10) + timedelta(hours=12),
        start_of_today - timedelta(days=14) + timedelta(hours=9),
        start_of_today - timedelta(days=21) + timedelta(hours=17),
        start_of_today - timedelta(days=30) + timedelta(hours=13),
        start_of_today - timedelta(days=45) + timedelta(hours=11),
    )

    items: list[dict[str, Any]] = []
    for index, (conversation, updated_at) in enumerate(
        zip(_CONVERSATIONS, updated_at_values, strict=True),
        start=1,
    ):
        chat_id = _seed_uuid7(index)
        first_turn_id = _seed_uuid7(100 + index * 2)
        second_turn_id = _seed_uuid7(101 + index * 2)
        created_at = updated_at - timedelta(minutes=10)
        first_answered_at = created_at + timedelta(minutes=1)
        follow_up_at = updated_at - timedelta(minutes=1)
        items.extend(
            (
                _chat_item(
                    chat_id=chat_id,
                    title=conversation.title,
                    created_at=first_answered_at,
                    updated_at=updated_at,
                ),
                _message_item(
                    chat_id=chat_id,
                    turn_id=first_turn_id,
                    sender="user",
                    content=conversation.first_question,
                    sent_at=created_at,
                ),
                _message_item(
                    chat_id=chat_id,
                    turn_id=first_turn_id,
                    sender="llm",
                    content=conversation.first_answer,
                    sent_at=first_answered_at,
                ),
                _message_item(
                    chat_id=chat_id,
                    turn_id=second_turn_id,
                    sender="user",
                    content=conversation.follow_up_question,
                    sent_at=follow_up_at,
                ),
                _message_item(
                    chat_id=chat_id,
                    turn_id=second_turn_id,
                    sender="llm",
                    content=conversation.follow_up_answer,
                    sent_at=updated_at,
                ),
            )
        )
    return tuple(items)


def _chat_item(
    *,
    chat_id: UUID,
    title: str,
    created_at: datetime,
    updated_at: datetime,
) -> dict[str, Any]:
    return {
        "pk": f"CHAT#{chat_id}",
        "sk": "CHAT",
        "entity_type": "chat",
        "chat_id": str(chat_id),
        "session_id": f"local-seed-{chat_id}",
        "title": title,
        "user_id": str(_USER_ID),
        "created_at": _format_datetime(created_at),
        "last_updated_at": _format_datetime(updated_at),
        "version": 1,
        "gsi1pk": f"USER#{_USER_ID}",
        "gsi1sk": f"UPDATED#{_format_datetime(updated_at)}#{chat_id}",
    }


def _message_item(
    *,
    chat_id: UUID,
    turn_id: UUID,
    sender: str,
    content: str,
    sent_at: datetime,
) -> dict[str, Any]:
    sender_order = "0" if sender == "user" else "1"
    formatted_sent_at = _format_datetime(sent_at)
    return {
        "pk": f"CHAT#{chat_id}",
        "sk": f"MESSAGE#{formatted_sent_at}#{turn_id}#{sender_order}",
        "entity_type": "message",
        "chat_id": str(chat_id),
        "turn_id": str(turn_id),
        "sender": sender,
        "content": content,
        "sent_at": formatted_sent_at,
    }


def _format_datetime(value: datetime) -> str:
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _seed_uuid7(index: int) -> UUID:
    # seedは冪等性が必要なため、固定値のままUUID v7形式に揃える。
    return UUID(f"019ecde4-0000-7000-8000-{index:012x}")


def _serialize(item: dict[str, Any]) -> dict[str, Any]:
    return {key: _serializer.serialize(value) for key, value in item.items()}


def _delete_partition(client: Any, *, table_name: str, partition_key: str) -> None:
    request = {
        "TableName": table_name,
        "KeyConditionExpression": "pk = :pk",
        "ExpressionAttributeValues": _serialize({":pk": partition_key}),
    }
    while True:
        response = client.query(**request)
        for item in response.get("Items", []):
            client.delete_item(
                TableName=table_name,
                Key={"pk": item["pk"], "sk": item["sk"]},
            )
        last_evaluated_key = response.get("LastEvaluatedKey")
        if last_evaluated_key is None:
            return
        request["ExclusiveStartKey"] = last_evaluated_key
