import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import {
    groupChatsByUpdatedAt,
    isChatContinuationExpired,
} from "@/features/chat/utils/chat-data";
import type { ChatSummary } from "@/lib/chat-api";

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

describe("isChatContinuationExpired", () => {
    const now = new Date("2026-06-10T12:00:00Z");

    test.each([
        ["24時間未満", "2026-06-09T12:00:00.001Z", false],
        ["ちょうど24時間", "2026-06-09T12:00:00.000Z", true],
        ["24時間超過", "2026-06-09T11:59:59.999Z", true],
    ])("%sを判定する", (_, updatedAt, expected) => {
        expect(isChatContinuationExpired(updatedAt, now)).toBe(expected);
    });
});
