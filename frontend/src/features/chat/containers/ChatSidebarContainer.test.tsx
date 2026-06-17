import { useAuthenticator } from "@aws-amplify/ui-react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { ChatSidebarContainer } from "@/features/chat/containers/ChatSidebarContainer";

vi.mock("@aws-amplify/ui-react", () => ({
    useAuthenticator: vi.fn(),
}));

describe("ChatSidebarContainer", () => {
    test("ログインユーザーのメールアドレスとイニシャルを表示する", () => {
        vi.mocked(useAuthenticator).mockReturnValue({
            signOut: vi.fn(),
            user: {
                signInDetails: {
                    loginId: "kei.h@example.com",
                },
            },
        } as unknown as ReturnType<typeof useAuthenticator>);

        render(
            <ChatSidebarContainer
                chats={[]}
                chatsError={false}
                isLoading={false}
                onChatSelect={vi.fn()}
                onNewChat={vi.fn()}
            />,
        );

        expect(screen.getByText("kei.h@example.com")).toBeInTheDocument();
        expect(screen.getByText("KH")).toBeInTheDocument();
    });

    test("ログアウトメニューを選ぶとサインアウトして選択後処理を呼ぶ", () => {
        const signOut = vi.fn();
        const onSelect = vi.fn();
        vi.mocked(useAuthenticator).mockReturnValue({
            signOut,
            user: {
                username: "paperbuddy-user",
            },
        } as unknown as ReturnType<typeof useAuthenticator>);

        render(
            <ChatSidebarContainer
                chats={[]}
                chatsError={false}
                isLoading={false}
                onChatSelect={vi.fn()}
                onNewChat={vi.fn()}
                onSelect={onSelect}
            />,
        );

        fireEvent.pointerDown(
            screen.getByRole("button", { name: "アカウントメニュー" }),
            { button: 0, ctrlKey: false },
        );
        fireEvent.click(screen.getByText("ログアウト"));

        expect(signOut).toHaveBeenCalledOnce();
        expect(onSelect).toHaveBeenCalledOnce();
    });
});
