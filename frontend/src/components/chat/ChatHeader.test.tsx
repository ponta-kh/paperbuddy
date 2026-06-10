import { render, screen } from "@testing-library/react";
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
    onMobileMenuOpenChange: vi.fn(),
    onNewChat: vi.fn(),
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
});
