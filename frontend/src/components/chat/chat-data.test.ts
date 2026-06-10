import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import type { ChatSummary } from "@/lib/chat-api";
import { groupChatsByUpdatedAt } from "./chat-data";

function createChat(id: string, updatedAt: Date): ChatSummary {
    return {
        id,
        title: `チャット${id}`,
        updatedAt: updatedAt.toISOString(),
    };
}

describe("groupChatsByUpdatedAt", () => {
    beforeEach(() => {
        vi.useFakeTimers();
        vi.setSystemTime(new Date(2026, 5, 10, 12));
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    test("更新日時を今日、過去7日間、1週間以上前に分類する", () => {
        const chats = [
            createChat("today", new Date(2026, 5, 10, 0)),
            createChat("within-seven-days", new Date(2026, 5, 9, 23, 59, 59)),
            createChat("seven-days-ago", new Date(2026, 5, 3, 0)),
            createChat("older", new Date(2026, 5, 2, 23, 59, 59)),
        ];

        const groups = groupChatsByUpdatedAt(chats);

        expect(groups).toEqual([
            { label: "今日", chats: [chats[0]] },
            { label: "過去7日間", chats: [chats[1], chats[2]] },
            { label: "1週間以上前", chats: [chats[3]] },
        ]);
    });

    test("チャットがない場合もすべての区分を返す", () => {
        expect(groupChatsByUpdatedAt([])).toEqual([
            { label: "今日", chats: [] },
            { label: "過去7日間", chats: [] },
            { label: "1週間以上前", chats: [] },
        ]);
    });
});
