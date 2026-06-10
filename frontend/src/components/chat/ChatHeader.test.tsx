import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ComponentProps } from "react";
import { describe, expect, test, vi } from "vitest";

import { TooltipProvider } from "@/components/shadcn/tooltip";
import { ChatHeader } from "./ChatHeader";

vi.mock("@/components/library/LibraryHeaderActions", () => ({
    LibraryHeaderActions: () => <div>ライブラリアクション</div>,
}));

const defaultProps: ComponentProps<typeof ChatHeader> = {
    chats: [],
    chatsError: false,
    isChatsLoading: false,
    mobileMenuOpen: false,
    sidebarOpen: true,
    onChatSelect: vi.fn(),
    onDeleteChat: vi.fn(),
    onMobileMenuOpenChange: vi.fn(),
    onNewChat: vi.fn(),
    onRenameChat: vi.fn(),
    onSidebarOpenChange: vi.fn(),
};

function renderHeader(props: Partial<ComponentProps<typeof ChatHeader>> = {}) {
    return render(
        <TooltipProvider>
            <ChatHeader {...defaultProps} {...props} />
        </TooltipProvider>,
    );
}

describe("ChatHeader", () => {
    test("新しいチャットではタイトルメニューを表示しない", () => {
        renderHeader();

        expect(
            screen.queryByRole("button", { name: "新しいチャット" }),
        ).not.toBeInTheDocument();
    });

    test("既存チャットではタイトルメニューを表示する", () => {
        renderHeader({
            selectedChatId: "chat-id",
            title: "既存チャット",
        });

        expect(
            screen.getByRole("button", { name: "既存チャット" }),
        ).toBeInTheDocument();
    });

    test("タイトル変更ダイアログから入力したタイトルで更新する", async () => {
        const onRenameChat = vi.fn().mockResolvedValue(undefined);
        renderHeader({
            selectedChatId: "chat-id",
            title: "変更前のタイトル",
            onRenameChat,
        });

        fireEvent.pointerDown(
            screen.getByRole("button", { name: "変更前のタイトル" }),
            { button: 0, ctrlKey: false },
        );
        fireEvent.click(await screen.findByText("タイトルを変更"));
        const input = await screen.findByRole("textbox", {
            name: "新しいタイトル",
        });
        fireEvent.change(input, { target: { value: "変更後のタイトル" } });
        fireEvent.click(screen.getByRole("button", { name: "更新" }));

        await waitFor(() => {
            expect(onRenameChat).toHaveBeenCalledWith("変更後のタイトル");
        });
    });

    test("削除確認ダイアログからチャットを削除する", async () => {
        const onDeleteChat = vi.fn().mockResolvedValue(undefined);
        renderHeader({
            selectedChatId: "chat-id",
            title: "削除対象",
            onDeleteChat,
        });

        fireEvent.pointerDown(
            screen.getByRole("button", { name: "削除対象" }),
            { button: 0, ctrlKey: false },
        );
        fireEvent.click(await screen.findByText("チャットを削除"));
        fireEvent.click(
            await screen.findByRole("button", {
                name: "削除",
            }),
        );

        await waitFor(() => {
            expect(onDeleteChat).toHaveBeenCalledOnce();
        });
    });
});
