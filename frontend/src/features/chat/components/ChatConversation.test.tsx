import { render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { ChatConversation } from "@/features/chat/components/ChatConversation";

describe("ChatConversation", () => {
    test("送信失敗したユーザーメッセージに失敗表示を付ける", () => {
        render(
            <ChatConversation
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
});
