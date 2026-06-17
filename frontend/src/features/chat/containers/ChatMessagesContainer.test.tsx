import {
    act,
    fireEvent,
    render,
    screen,
    waitFor,
} from "@testing-library/react";
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

    test("チャットを切り替えると履歴を取得する", async () => {
        vi.mocked(getChatMessages)
            .mockResolvedValueOnce([])
            .mockResolvedValueOnce([
                {
                    id: "turn-2:user",
                    role: "user",
                    content: "切り替え後",
                    createdAt: "2026-01-02T00:00:00Z",
                },
            ]);

        const { rerender } = render(
            <ChatMessagesContainer selectedChatId="chat-1">
                {({ messages }) => <div>{messages[0]?.content}</div>}
            </ChatMessagesContainer>,
        );

        await waitFor(() => {
            expect(getChatMessages).toHaveBeenCalledOnce();
        });

        rerender(
            <ChatMessagesContainer selectedChatId="chat-2">
                {({ messages }) => <div>{messages[0]?.content}</div>}
            </ChatMessagesContainer>,
        );

        await waitFor(() => {
            expect(getChatMessages).toHaveBeenCalledTimes(2);
        });
        expect(screen.getByText("切り替え後")).toBeInTheDocument();
    });

    test("ユーザーメッセージを即時追加し失敗状態へ更新する", async () => {
        vi.mocked(getChatMessages).mockResolvedValue([]);

        render(
            <ChatMessagesContainer>
                {({ messages, onAppendUserMessage, onMarkMessageFailed }) => (
                    <div>
                        <span>
                            {messages
                                .map(
                                    (message) =>
                                        `${message.content}:${message.status}`,
                                )
                                .join(",")}
                        </span>
                        <button
                            type="button"
                            onClick={() => {
                                const id = onAppendUserMessage("質問です");
                                onMarkMessageFailed(id);
                            }}
                        >
                            送信
                        </button>
                    </div>
                )}
            </ChatMessagesContainer>,
        );

        fireEvent.click(screen.getByRole("button", { name: "送信" }));

        expect(screen.getByText("質問です:failed")).toBeInTheDocument();
        expect(getChatMessages).not.toHaveBeenCalled();
    });

    test("回答を段階的に表示する", () => {
        vi.useFakeTimers();

        render(
            <ChatMessagesContainer>
                {({ messages, onAppendAssistantMessage }) => (
                    <div>
                        <span>{messages[0]?.content}</span>
                        <span>
                            {messages[0]?.citations?.[0]?.sources[0]?.content}
                        </span>
                        <button
                            type="button"
                            onClick={() =>
                                onAppendAssistantMessage("回答テキスト", [
                                    {
                                        text: "回答",
                                        spanStart: 0,
                                        spanEnd: 2,
                                        sources: [
                                            {
                                                content: "引用抜粋",
                                                locationType: "S3",
                                                uri: "s3://bucket/paper.pdf",
                                                metadata: {},
                                            },
                                        ],
                                    },
                                ])
                            }
                        >
                            回答追加
                        </button>
                    </div>
                )}
            </ChatMessagesContainer>,
        );

        fireEvent.click(screen.getByRole("button", { name: "回答追加" }));
        expect(screen.queryByText("回答テキスト")).not.toBeInTheDocument();
        expect(screen.getByText("引用抜粋")).toBeInTheDocument();

        act(() => vi.advanceTimersByTime(20));
        expect(screen.getByText("回答")).toBeInTheDocument();

        act(() => vi.runAllTimers());
        expect(screen.getByText("回答テキスト")).toBeInTheDocument();

        vi.useRealTimers();
    });

    test("新規チャット採番後は履歴を再取得しない", async () => {
        vi.mocked(getChatMessages).mockResolvedValue([]);

        const { rerender } = render(
            <ChatMessagesContainer>
                {({ onBindCurrentChat }) => (
                    <button
                        type="button"
                        onClick={() => onBindCurrentChat("chat-new")}
                    >
                        採番
                    </button>
                )}
            </ChatMessagesContainer>,
        );

        fireEvent.click(screen.getByRole("button", { name: "採番" }));
        rerender(
            <ChatMessagesContainer selectedChatId="chat-new">
                {() => <div>messages</div>}
            </ChatMessagesContainer>,
        );

        await waitFor(() => {
            expect(getChatMessages).not.toHaveBeenCalled();
        });
    });

    test("新規チャット採番後も追加済み回答の段階表示を継続する", () => {
        vi.useFakeTimers();
        vi.mocked(getChatMessages).mockResolvedValue([]);

        const { rerender } = render(
            <ChatMessagesContainer>
                {({
                    messages,
                    onAppendAssistantMessage,
                    onBindCurrentChat,
                }) => (
                    <div>
                        <span>{messages[0]?.content}</span>
                        <button
                            type="button"
                            onClick={() => {
                                onBindCurrentChat("chat-new");
                                onAppendAssistantMessage("新しい回答", []);
                            }}
                        >
                            回答追加
                        </button>
                    </div>
                )}
            </ChatMessagesContainer>,
        );

        fireEvent.click(screen.getByRole("button", { name: "回答追加" }));
        rerender(
            <ChatMessagesContainer selectedChatId="chat-new">
                {({ messages }) => <div>{messages[0]?.content}</div>}
            </ChatMessagesContainer>,
        );

        act(() => vi.runAllTimers());

        expect(screen.getByText("新しい回答")).toBeInTheDocument();
        expect(getChatMessages).not.toHaveBeenCalled();

        vi.useRealTimers();
    });
});
