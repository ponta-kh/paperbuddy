import type { ReactNode } from "react";
import { ChatMobileSidebarSheet } from "@/features/chat/components/ChatHeaderContainer/ChatMobileSidebarSheet";
import { ChatSelectedChatActions } from "@/features/chat/components/ChatHeaderContainer/ChatSelectedChatActions";
import { ChatSidebarToggleButton } from "@/features/chat/components/ChatHeaderContainer/ChatSidebarToggleButton";

type ChatHeaderContainerProps = {
    mobileSidebar: ReactNode;
    mobileMenuOpen: boolean;
    selectedChatId?: string;
    sidebarOpen: boolean;
    title?: string;
    onDeleteChat: () => Promise<void>;
    onMobileMenuOpenChange: (open: boolean) => void;
    onRenameChat: (title: string) => Promise<void>;
    onSidebarOpenChange: (open: boolean) => void;
    headerActions?: ReactNode;
};

export function ChatHeaderContainer({
    mobileSidebar,
    mobileMenuOpen,
    selectedChatId,
    sidebarOpen,
    title,
    onDeleteChat,
    onMobileMenuOpenChange,
    onRenameChat,
    onSidebarOpenChange,
    headerActions,
}: ChatHeaderContainerProps) {
    return (
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-[#e8ebe8] bg-white/80 px-4 backdrop-blur-md sm:px-6">
            <div className="flex items-center gap-2">
                <ChatMobileSidebarSheet
                    open={mobileMenuOpen}
                    onOpenChange={onMobileMenuOpenChange}
                >
                    {mobileSidebar}
                </ChatMobileSidebarSheet>

                <ChatSidebarToggleButton
                    sidebarOpen={sidebarOpen}
                    onSidebarOpenChange={onSidebarOpenChange}
                />

                {selectedChatId && (
                    <ChatSelectedChatActions
                        title={title ?? "新しいチャット"}
                        onDeleteChat={onDeleteChat}
                        onRenameChat={onRenameChat}
                    />
                )}
            </div>

            {headerActions}
        </header>
    );
}
