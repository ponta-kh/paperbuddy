import { beforeEach, expect, test, vi } from "vitest";

import { requestJson } from "@/lib/api-client";
import { sendPrompt } from "@/lib/chat-api";

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
        title: "既存チャット",
        last_updated_at: "2026-06-15T00:01:00Z",
    });

    await sendPrompt("続きの質問", "chat/1");

    expect(requestJson).toHaveBeenCalledWith("/chats/chat%2F1/messages", {
        method: "POST",
        body: { prompt: "続きの質問" },
    });
});
