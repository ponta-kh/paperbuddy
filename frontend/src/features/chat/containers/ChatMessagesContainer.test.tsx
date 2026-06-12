import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { ChatMessagesContainer } from "@/features/chat/containers/ChatMessagesContainer";
import { getChatMessages } from "@/lib/chat-api";

vi.mock("@/lib/chat-api", () => ({
    getChatMessages: vi.fn(),
}));

describe("ChatMessagesContainer", () => {
    beforeEach(() => {
        vi.mocked(getChatMessages).mockReset();
    });

    test("選択中チャットのメッセージを取得して渡す", async () => {
        vi.mocked(getChatMessages).mockResolvedValue([
            {
                id: "turn-1:user",
                role: "user",
                content: "質問です",
                createdAt: "2026-01-01T00:00:00Z",
            },
        ]);

        render(
            <ChatMessagesContainer selectedChatId="chat-1">
                {({ isLoading, messages }) => (
                    <div>
                        <span>{isLoading ? "loading" : "ready"}</span>
                        <span>{messages[0]?.content}</span>
                    </div>
                )}
            </ChatMessagesContainer>,
        );

        await waitFor(() => {
            expect(getChatMessages).toHaveBeenCalledOnce();
        });
        expect(screen.getByText("ready")).toBeInTheDocument();
        expect(screen.getByText("質問です")).toBeInTheDocument();
    });

    test("更新キーが変わると再取得する", async () => {
        vi.mocked(getChatMessages).mockResolvedValue([]);

        const { rerender } = render(
            <ChatMessagesContainer key={0} selectedChatId="chat-1">
                {() => <div>messages</div>}
            </ChatMessagesContainer>,
        );

        await waitFor(() => {
            expect(getChatMessages).toHaveBeenCalledOnce();
        });

        rerender(
            <ChatMessagesContainer key={1} selectedChatId="chat-1">
                {() => <div>messages</div>}
            </ChatMessagesContainer>,
        );

        await waitFor(() => {
            expect(getChatMessages).toHaveBeenCalledTimes(2);
        });
    });
});
