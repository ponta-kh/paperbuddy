import { ChevronDown, Menu, PanelLeftClose } from "lucide-react";

import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { LibraryHeaderActions } from "@/components/library/LibraryHeaderActions";
import { Button } from "@/components/shadcn/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/shadcn/dropdown-menu";
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
    onMobileMenuOpenChange: (open: boolean) => void;
    onNewChat: () => void;
    onSidebarOpenChange: (open: boolean) => void;
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
    onMobileMenuOpenChange,
    onNewChat,
    onSidebarOpenChange,
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

                <Separator orientation="vertical" className="mx-1 h-5" />

                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button
                            variant="ghost"
                            className="gap-2 rounded-lg px-2 text-[13px] font-medium text-[#344a42]"
                        >
                            <span className="max-w-44 truncate sm:max-w-none">
                                {title ?? "新しいチャット"}
                            </span>
                            <ChevronDown className="size-3.5 text-[#809089]" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start" className="w-52">
                        <DropdownMenuItem>タイトルを変更</DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="text-destructive">
                            チャットを削除
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>

            <LibraryHeaderActions />
        </header>
    );
}
