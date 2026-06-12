import { Menu, PanelLeftClose } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/shadcn/button";
import { Separator } from "@/components/shadcn/separator";
import {
    Sheet,
    SheetContent,
    SheetTitle,
    SheetTrigger,
} from "@/components/shadcn/sheet";
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from "@/components/shadcn/tooltip";
import { ChatActionsMenu } from "@/features/chat/components/ChatActionsMenu";
import { ChatSidebar } from "@/features/chat/components/ChatSidebar";
import type { ChatSummary } from "@/lib/chat-api";
import { cn } from "@/lib/utils";

type ChatHeaderProps = {
    chats: ChatSummary[];
    chatsError: boolean;
    isChatsLoading: boolean;
    mobileMenuOpen: boolean;
    selectedChatId?: string;
    sidebarOpen: boolean;
    title?: string;
    onChatSelect: (chatId: string) => void;
    onDeleteChat: () => Promise<void>;
    onMobileMenuOpenChange: (open: boolean) => void;
    onNewChat: () => void;
    onRenameChat: (title: string) => Promise<void>;
    onSidebarOpenChange: (open: boolean) => void;
    headerActions?: ReactNode;
};

export function ChatHeader({
    chats,
    chatsError,
    isChatsLoading,
    mobileMenuOpen,
    selectedChatId,
    sidebarOpen,
    title,
    onChatSelect,
    onDeleteChat,
    onMobileMenuOpenChange,
    onNewChat,
    onRenameChat,
    onSidebarOpenChange,
    headerActions,
}: ChatHeaderProps) {
    return (
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-[#e8ebe8] bg-white/80 px-4 backdrop-blur-md sm:px-6">
            <div className="flex items-center gap-2">
                <Sheet
                    open={mobileMenuOpen}
                    onOpenChange={onMobileMenuOpenChange}
                >
                    <SheetTrigger asChild>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="lg:hidden"
                            aria-label="メニューを開く"
                        >
                            <Menu />
                        </Button>
                    </SheetTrigger>
                    <SheetContent side="left" className="w-72 p-0">
                        <SheetTitle className="sr-only">
                            チャットメニュー
                        </SheetTitle>
                        <ChatSidebar
                            chats={chats}
                            chatsError={chatsError}
                            isLoading={isChatsLoading}
                            selectedChatId={selectedChatId}
                            onChatSelect={onChatSelect}
                            onNewChat={onNewChat}
                            onSelect={() => onMobileMenuOpenChange(false)}
                        />
                    </SheetContent>
                </Sheet>

                <Tooltip>
                    <TooltipTrigger asChild>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="hidden text-[#65756f] lg:inline-flex"
                            onClick={() => onSidebarOpenChange(!sidebarOpen)}
                            aria-label="サイドバーを切り替える"
                        >
                            <PanelLeftClose
                                className={cn(
                                    "transition-transform",
                                    !sidebarOpen && "rotate-180",
                                )}
                            />
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>サイドバーを切り替える</TooltipContent>
                </Tooltip>

                {selectedChatId && (
                    <>
                        <Separator
                            orientation="vertical"
                            className="mx-1 h-5"
                        />

                        <ChatActionsMenu
                            title={title ?? "新しいチャット"}
                            onDelete={onDeleteChat}
                            onRename={onRenameChat}
                        />
                    </>
                )}
            </div>

            {headerActions}
        </header>
    );
}
