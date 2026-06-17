import { render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { ChatConversationSection } from "@/features/chat/sections/ChatMessagesContainer/ChatConversationSection";

describe("ChatConversationSection", () => {
    test("送信失敗したユーザーメッセージに失敗表示を付ける", () => {
        render(
            <ChatConversationSection
                isLoading={false}
                isSending={false}
                loadError={false}
                messages={[
                    {
                        id: "temporary-user-message",
                        role: "user",
                        content: "質問です",
                        createdAt: "2026-01-01T00:00:00Z",
                        status: "failed",
                    },
                ]}
                onSuggestionSelect={vi.fn()}
            />,
        );

        expect(screen.getByText("質問です")).toBeInTheDocument();
        expect(screen.getByText("送信できませんでした")).toBeInTheDocument();
    });

    test("回答メッセージに引用情報を表示する", () => {
        render(
            <ChatConversationSection
                isLoading={false}
                isSending={false}
                loadError={false}
                messages={[
                    {
                        id: "assistant-message",
                        role: "assistant",
                        content: "回答です",
                        createdAt: "2026-01-01T00:00:01Z",
                        status: "completed",
                        citations: [
                            {
                                text: "回答です",
                                spanStart: 0,
                                spanEnd: 4,
                                sources: [
                                    {
                                        content: "根拠となる抜粋です",
                                        locationType: "S3",
                                        uri: "s3://bucket/paper.pdf",
                                        metadata: {
                                            title: "Paper Title",
                                            page: 3,
                                        },
                                    },
                                ],
                            },
                        ],
                    },
                ]}
                onSuggestionSelect={vi.fn()}
            />,
        );

        expect(screen.getByText("回答です")).toBeInTheDocument();
        expect(screen.getByText("引用 1件")).toBeInTheDocument();
        expect(screen.getByText("[1] Paper Title / p.3")).toBeInTheDocument();
        expect(screen.getByText("根拠となる抜粋です")).toBeInTheDocument();
    });
});
