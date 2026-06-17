import { useAuthenticator } from "@aws-amplify/ui-react";
import { Separator } from "@/components/shadcn/separator";
import { ChatAccountMenu } from "@/features/chat/components/ChatSidebarContainer/ChatAccountMenu";
import { ChatHistoryList } from "@/features/chat/components/ChatSidebarContainer/ChatHistoryList";
import { ChatNewChatButton } from "@/features/chat/components/ChatSidebarContainer/ChatNewChatButton";
import { ChatSidebarBrand } from "@/features/chat/components/ChatSidebarContainer/ChatSidebarBrand";
import { groupChatsByUpdatedAt } from "@/features/chat/utils/chat-data";
import type { ChatSummary } from "@/lib/chat-api";

type AuthUserDetails = {
    username?: string;
    signInDetails?: {
        loginId?: string;
    };
};

type ChatSidebarContainerProps = {
    chats: ChatSummary[];
    chatsError: boolean;
    isLoading: boolean;
    selectedChatId?: string;
    onChatSelect: (chatId: string) => void;
    onNewChat: () => void;
    onSelect?: () => void;
};

function createInitials(name: string): string {
    const source = name.trim();
    if (!source) return "PB";

    const localPart = source.split("@")[0] ?? source;
    const words = localPart.split(/[\s._-]+/).filter(Boolean);
    if (words.length >= 2) {
        return `${words[0][0]}${words[1][0]}`.toUpperCase();
    }

    return localPart.slice(0, 2).toUpperCase();
}

export function ChatSidebarContainer({
    chats,
    chatsError,
    isLoading,
    selectedChatId,
    onChatSelect,
    onNewChat,
    onSelect,
}: ChatSidebarContainerProps) {
    const { signOut, user } = useAuthenticator((context) => [
        context.signOut,
        context.user,
    ]);
    const userDetails = user as AuthUserDetails | undefined;
    const displayName =
        userDetails?.signInDetails?.loginId ??
        userDetails?.username ??
        "PaperBuddyユーザー";
    const chatGroups = groupChatsByUpdatedAt(chats);

    const handleNewChat = () => {
        onNewChat();
        onSelect?.();
    };

    const handleChatSelect = (chatId: string) => {
        onChatSelect(chatId);
        onSelect?.();
    };

    const handleSignOut = () => {
        signOut();
        onSelect?.();
    };

    return (
        <div className="flex h-full flex-col bg-[#f7f8f6]">
            <ChatSidebarBrand />
            <ChatNewChatButton onNewChat={handleNewChat} />
            <Separator className="mx-4 my-4 w-auto bg-[#dfe4df]" />
            <ChatHistoryList
                chatGroups={chatGroups}
                chatsError={chatsError}
                isLoading={isLoading}
                selectedChatId={selectedChatId}
                onChatSelect={handleChatSelect}
            />
            <ChatAccountMenu
                account={{
                    displayName,
                    initials: createInitials(displayName),
                }}
                onSignOut={handleSignOut}
            />
        </div>
    );
}
