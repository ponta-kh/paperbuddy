import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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

    test("新しいチャットを一覧の先頭へ追加する", async () => {
        vi.mocked(getChats).mockResolvedValue([
            {
                id: "chat-1",
                title: "最初のチャット",
                updatedAt: "2026-01-01T00:00:00Z",
            },
        ]);

        render(
            <ChatThreadsContainer>
                {({ chats, onUpsertChat }) => (
                    <div>
                        <span>{chats.map((chat) => chat.id).join(",")}</span>
                        <button
                            type="button"
                            onClick={() =>
                                onUpsertChat({
                                    id: "chat-2",
                                    title: "新しいチャット",
                                    updatedAt: "2026-01-02T00:00:00Z",
                                })
                            }
                        >
                            追加
                        </button>
                    </div>
                )}
            </ChatThreadsContainer>,
        );

        await waitFor(() => {
            expect(getChats).toHaveBeenCalledOnce();
        });
        fireEvent.click(screen.getByRole("button", { name: "追加" }));

        expect(screen.getByText("chat-2,chat-1")).toBeInTheDocument();
        expect(getChats).toHaveBeenCalledOnce();
    });

    test("既存チャットを更新して一覧の先頭へ移動する", async () => {
        vi.mocked(getChats).mockResolvedValue([
            {
                id: "chat-1",
                title: "最初のチャット",
                updatedAt: "2026-01-02T00:00:00Z",
            },
            {
                id: "chat-2",
                title: "古いタイトル",
                updatedAt: "2026-01-01T00:00:00Z",
            },
        ]);

        render(
            <ChatThreadsContainer>
                {({ chats, onUpsertChat }) => (
                    <div>
                        <span>
                            {chats
                                .map((chat) => `${chat.id}:${chat.title}`)
                                .join(",")}
                        </span>
                        <button
                            type="button"
                            onClick={() =>
                                onUpsertChat({
                                    id: "chat-2",
                                    title: "更新後タイトル",
                                    updatedAt: "2026-01-03T00:00:00Z",
                                })
                            }
                        >
                            更新
                        </button>
                    </div>
                )}
            </ChatThreadsContainer>,
        );

        await waitFor(() => {
            expect(getChats).toHaveBeenCalledOnce();
        });
        fireEvent.click(screen.getByRole("button", { name: "更新" }));

        expect(
            screen.getByText("chat-2:更新後タイトル,chat-1:最初のチャット"),
        ).toBeInTheDocument();
        expect(getChats).toHaveBeenCalledOnce();
    });
});
