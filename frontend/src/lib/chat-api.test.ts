import { beforeEach, expect, test, vi } from "vitest";

import { requestJson } from "@/lib/api-client";
import { getChatMessages, sendPrompt } from "@/lib/chat-api";

vi.mock("@/lib/api-client", () => ({
    requestJson: vi.fn(),
}));

beforeEach(() => {
    vi.mocked(requestJson).mockReset();
});

test("初回送信結果をサイドバー情報と回答へ変換する", async () => {
    vi.mocked(requestJson).mockResolvedValue({
        chat_id: "chat-1",
        answer: "生成された回答",
        citations: [
            {
                text: "生成された回答",
                span_start: 0,
                span_end: 6,
                sources: [
                    {
                        content: "引用抜粋",
                        location_type: "S3",
                        uri: "s3://bucket/paper.pdf",
                        metadata: { title: "Paper Title", page: 3 },
                    },
                ],
            },
        ],
        title: "新しいチャット",
        last_updated_at: "2026-06-15T00:00:00Z",
    });

    await expect(sendPrompt("質問です")).resolves.toEqual({
        chat: {
            id: "chat-1",
            title: "新しいチャット",
            updatedAt: "2026-06-15T00:00:00Z",
        },
        answer: "生成された回答",
        citations: [
            {
                text: "生成された回答",
                spanStart: 0,
                spanEnd: 6,
                sources: [
                    {
                        content: "引用抜粋",
                        locationType: "S3",
                        uri: "s3://bucket/paper.pdf",
                        metadata: { title: "Paper Title", page: 3 },
                    },
                ],
            },
        ],
    });
    expect(requestJson).toHaveBeenCalledWith("/chats", {
        method: "POST",
        body: { prompt: "質問です" },
    });
});

test("継続送信では対象チャットのメッセージAPIを呼び出す", async () => {
    vi.mocked(requestJson).mockResolvedValue({
        chat_id: "chat/1",
        answer: "継続回答",
        citations: [],
        title: "既存チャット",
        last_updated_at: "2026-06-15T00:01:00Z",
    });

    await sendPrompt("続きの質問", "chat/1");

    expect(requestJson).toHaveBeenCalledWith("/chats/chat%2F1/messages", {
        method: "POST",
        body: { prompt: "続きの質問" },
    });
});

test("履歴取得結果の引用情報をメッセージへ変換する", async () => {
    vi.mocked(requestJson).mockResolvedValue({
        chat_id: "chat-1",
        messages: [
            {
                request_id: "request-1",
                sender: "llm",
                content: "履歴回答",
                citations: [
                    {
                        text: "履歴回答",
                        span_start: 0,
                        span_end: 4,
                        sources: [
                            {
                                content: "履歴引用抜粋",
                                location_type: "S3",
                                uri: "s3://bucket/history.pdf",
                                metadata: { title: "History Paper", page: 5 },
                            },
                        ],
                    },
                ],
                sent_at: "2026-06-15T00:02:00Z",
            },
        ],
    });

    await expect(getChatMessages("chat-1")).resolves.toEqual([
        {
            id: "request-1:llm",
            role: "assistant",
            content: "履歴回答",
            citations: [
                {
                    text: "履歴回答",
                    spanStart: 0,
                    spanEnd: 4,
                    sources: [
                        {
                            content: "履歴引用抜粋",
                            locationType: "S3",
                            uri: "s3://bucket/history.pdf",
                            metadata: { title: "History Paper", page: 5 },
                        },
                    ],
                },
            ],
            createdAt: "2026-06-15T00:02:00Z",
        },
    ]);
});
