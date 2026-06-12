import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { ChatThreadsContainer } from "@/features/chat/containers/ChatThreadsContainer";
import { deleteChat, getChats, renameChat } from "@/lib/chat-api";

vi.mock("@/lib/chat-api", () => ({
    deleteChat: vi.fn(),
    getChats: vi.fn(),
    renameChat: vi.fn(),
}));

describe("ChatThreadsContainer", () => {
    beforeEach(() => {
        vi.mocked(getChats).mockReset();
        vi.mocked(renameChat).mockReset();
        vi.mocked(deleteChat).mockReset();
    });

    test("チャット一覧を取得して選択中タイトルを渡す", async () => {
        vi.mocked(getChats).mockResolvedValue([
            {
                id: "chat-1",
                title: "最初のチャット",
                updatedAt: "2026-01-01T00:00:00Z",
            },
        ]);

        render(
            <ChatThreadsContainer selectedChatId="chat-1">
                {({ isLoading, title }) => (
                    <div>
                        <span>{isLoading ? "loading" : "ready"}</span>
                        <span>{title}</span>
                    </div>
                )}
            </ChatThreadsContainer>,
        );

        await waitFor(() => {
            expect(getChats).toHaveBeenCalledOnce();
        });
        expect(screen.getByText("ready")).toBeInTheDocument();
        expect(screen.getByText("最初のチャット")).toBeInTheDocument();
    });

    test("更新キーが変わると再取得する", async () => {
        vi.mocked(getChats).mockResolvedValue([
            {
                id: "chat-1",
                title: "最初のチャット",
                updatedAt: "2026-01-01T00:00:00Z",
            },
        ]);

        const { rerender } = render(
            <ChatThreadsContainer key={0}>
                {() => <div>threads</div>}
            </ChatThreadsContainer>,
        );

        await waitFor(() => {
            expect(getChats).toHaveBeenCalledOnce();
        });

        rerender(
            <ChatThreadsContainer key={1}>
                {() => <div>threads</div>}
            </ChatThreadsContainer>,
        );

        await waitFor(() => {
            expect(getChats).toHaveBeenCalledTimes(2);
        });
    });
});
