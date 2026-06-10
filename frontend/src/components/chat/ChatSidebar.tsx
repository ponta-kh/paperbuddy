import {
    BookOpen,
    LoaderCircle,
    MessageSquareText,
    MoreHorizontal,
    Plus,
    Settings,
} from "lucide-react";

import { groupChatsByUpdatedAt } from "@/components/chat/chat-data";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import { Button } from "@/components/shadcn/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/shadcn/dropdown-menu";
import { ScrollArea } from "@/components/shadcn/scroll-area";
import { Separator } from "@/components/shadcn/separator";
import type { ChatSummary } from "@/lib/chat-api";
import { cn } from "@/lib/utils";

type ChatSidebarProps = {
    chats: ChatSummary[];
    chatsError: boolean;
    isLoading: boolean;
    selectedChatId?: string;
    onChatSelect: (chatId: string) => void;
    onNewChat: () => void;
    onSelect?: () => void;
};

export function ChatSidebar({
    chats,
    chatsError,
    isLoading,
    selectedChatId,
    onChatSelect,
    onNewChat,
    onSelect,
}: ChatSidebarProps) {
    const chatGroups = groupChatsByUpdatedAt(chats);

    return (
        <div className="flex h-full flex-col bg-[#f7f8f6]">
            <div className="flex h-16 items-center gap-2 px-4">
                <div className="flex size-8 items-center justify-center rounded-xl bg-[#163d32] text-white shadow-sm">
                    <BookOpen className="size-4" strokeWidth={2.25} />
                </div>
                <span className="text-[17px] font-semibold tracking-tight text-[#18352d]">
                    PaperBuddy
                </span>
            </div>

            <div className="px-3 pb-3">
                <Button
                    className="h-10 w-full justify-start gap-2.5 rounded-xl bg-[#163d32] px-3 text-white shadow-sm hover:bg-[#214e41]"
                    onClick={() => {
                        onNewChat();
                        onSelect?.();
                    }}
                >
                    <Plus className="size-4" />
                    新しいチャット
                </Button>
            </div>

            <Separator className="mx-4 my-4 w-auto bg-[#dfe4df]" />

            <ScrollArea className="min-h-0 flex-1 px-3">
                <div className="space-y-5 pb-5">
                    {isLoading && (
                        <div className="flex items-center gap-2 px-3 py-2 text-xs text-[#7b8984]">
                            <LoaderCircle className="size-3.5 animate-spin" />
                            履歴を読み込んでいます
                        </div>
                    )}
                    {chatsError && (
                        <p className="px-3 py-2 text-xs leading-5 text-destructive">
                            チャット履歴を取得できませんでした。
                        </p>
                    )}
                    {!isLoading && !chatsError && chats.length === 0 && (
                        <p className="px-3 py-2 text-xs leading-5 text-[#87948f]">
                            まだチャット履歴がありません。
                        </p>
                    )}
                    {!isLoading &&
                        !chatsError &&
                        chatGroups.map((group) => (
                            <div key={group.label}>
                                <p className="mb-1.5 px-3 text-[11px] font-medium tracking-wide text-[#8a9792]">
                                    {group.label}
                                </p>
                                <div className="space-y-0.5">
                                    {group.chats.map((chat) => (
                                        <button
                                            type="button"
                                            key={chat.id}
                                            onClick={() => {
                                                onChatSelect(chat.id);
                                                onSelect?.();
                                            }}
                                            className={cn(
                                                "group flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-[13px] text-[#4e5e58] transition-colors hover:bg-[#e9ece8]",
                                                selectedChatId === chat.id &&
                                                    "bg-[#e7ece8] font-medium text-[#18352d]",
                                            )}
                                        >
                                            <MessageSquareText className="size-3.5 shrink-0 opacity-60" />
                                            <span className="truncate">
                                                {chat.title}
                                            </span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ))}
                </div>
            </ScrollArea>

            <div className="border-t border-[#dfe4df] p-3">
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <button
                            type="button"
                            className="flex w-full items-center gap-3 rounded-xl p-2 text-left transition-colors hover:bg-[#e9ece8]"
                        >
                            <Avatar>
                                <AvatarFallback className="bg-[#dce8e1] text-xs font-semibold text-[#245445]">
                                    KH
                                </AvatarFallback>
                            </Avatar>
                            <div className="min-w-0 flex-1">
                                <p className="truncate text-[13px] font-medium text-[#263b34]">
                                    Kei H.
                                </p>
                                <p className="truncate text-[11px] text-[#7b8984]">
                                    Personal workspace
                                </p>
                            </div>
                            <MoreHorizontal className="size-4 text-[#7b8984]" />
                        </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-52">
                        <DropdownMenuItem>
                            <Settings />
                            設定
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem>ログアウト</DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
        </div>
    );
}
