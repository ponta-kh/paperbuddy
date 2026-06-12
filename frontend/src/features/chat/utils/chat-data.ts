import type { ChatSummary } from "@/lib/chat-api";

export type ChatGroup = {
    label: "今日" | "過去7日間" | "1週間以上前";
    chats: ChatSummary[];
};

export function groupChatsByUpdatedAt(chats: ChatSummary[]): ChatGroup[] {
    const now = new Date();
    const startOfToday = new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate(),
    );
    const sevenDaysAgo = new Date(startOfToday);
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    const groups: ChatGroup[] = [
        { label: "今日", chats: [] },
        { label: "過去7日間", chats: [] },
        { label: "1週間以上前", chats: [] },
    ];

    for (const chat of chats) {
        const updatedAt = new Date(chat.updatedAt);

        if (updatedAt >= startOfToday) {
            groups[0].chats.push(chat);
        } else if (updatedAt >= sevenDaysAgo) {
            groups[1].chats.push(chat);
        } else {
            groups[2].chats.push(chat);
        }
    }

    return groups;
}

export const suggestions = [
    "この論文群の主要な研究課題を整理して",
    "手法ごとの精度と計算コストを比較して",
    "今後の研究課題として挙げられている点は？",
];
