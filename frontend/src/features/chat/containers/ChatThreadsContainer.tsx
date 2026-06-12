import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import {
    type ChatSummary,
    deleteChat,
    getChats,
    renameChat,
} from "@/lib/chat-api";

type ChatThreadsContainerProps = {
    selectedChatId?: string;
    children: (state: {
        chats: ChatSummary[];
        chatsError: boolean;
        isLoading: boolean;
        title?: string;
        onDeleteChat: () => Promise<void>;
        onRenameChat: (title: string) => Promise<void>;
    }) => ReactNode;
};

export function ChatThreadsContainer({
    selectedChatId,
    children,
}: ChatThreadsContainerProps) {
    const [chats, setChats] = useState<ChatSummary[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [chatsError, setChatsError] = useState(false);

    useEffect(() => {
        const controller = new AbortController();

        setIsLoading(true);

        getChats(controller.signal)
            .then((response) => {
                setChats(response);
                setChatsError(false);
            })
            .catch((error: unknown) => {
                if (
                    error instanceof DOMException &&
                    error.name === "AbortError"
                )
                    return;
                setChatsError(true);
            })
            .finally(() => {
                if (!controller.signal.aborted) setIsLoading(false);
            });

        return () => controller.abort();
    }, []);

    const selectedChat = chats.find((chat) => chat.id === selectedChatId);

    const handleRenameChat = async (title: string) => {
        if (!selectedChatId) return;

        await renameChat(selectedChatId, title);
        setChats((currentChats) =>
            currentChats.map((chat) =>
                chat.id === selectedChatId ? { ...chat, title } : chat,
            ),
        );
    };

    const handleDeleteChat = async () => {
        if (!selectedChatId) return;

        await deleteChat(selectedChatId);
        setChats((currentChats) =>
            currentChats.filter((chat) => chat.id !== selectedChatId),
        );
    };

    return children({
        chats,
        chatsError,
        isLoading,
        title: selectedChat?.title,
        onDeleteChat: handleDeleteChat,
        onRenameChat: handleRenameChat,
    });
}
