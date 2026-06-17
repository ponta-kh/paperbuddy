import { LoaderCircle, MessageSquareText } from "lucide-react";
import { ScrollArea } from "@/components/shadcn/scroll-area";
import type { ChatGroup } from "@/features/chat/utils/chat-data";
import { cn } from "@/lib/utils";

type ChatHistoryListProps = {
    chatGroups: ChatGroup[];
    chatsError: boolean;
    isLoading: boolean;
    selectedChatId?: string;
    onChatSelect: (chatId: string) => void;
};

export function ChatHistoryList({
    chatGroups,
    chatsError,
    isLoading,
    selectedChatId,
    onChatSelect,
}: ChatHistoryListProps) {
    const chatCount = chatGroups.reduce(
        (total, group) => total + group.chats.length,
        0,
    );

    return (
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
                {!isLoading && !chatsError && chatCount === 0 && (
                    <p className="px-3 py-2 text-xs leading-5 text-[#87948f]">
                        まだチャット履歴がありません。
                    </p>
                )}
                {!isLoading &&
                    !chatsError &&
                    chatCount > 0 &&
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
                                        onClick={() => onChatSelect(chat.id)}
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
    );
}
