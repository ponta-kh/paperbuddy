import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import { type ChatMessage, getChatMessages } from "@/lib/chat-api";

type ChatMessagesContainerProps = {
    selectedChatId?: string;
    children: (state: {
        messages: ChatMessage[];
        isLoading: boolean;
        loadError: boolean;
    }) => ReactNode;
};

export function ChatMessagesContainer({
    selectedChatId,
    children,
}: ChatMessagesContainerProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [loadError, setLoadError] = useState(false);

    useEffect(() => {
        if (!selectedChatId) {
            setMessages([]);
            setLoadError(false);
            setIsLoading(false);
            return;
        }

        const controller = new AbortController();
        setIsLoading(true);

        getChatMessages(selectedChatId, controller.signal)
            .then((response) => {
                setMessages(response);
                setLoadError(false);
            })
            .catch((error: unknown) => {
                if (
                    error instanceof DOMException &&
                    error.name === "AbortError"
                )
                    return;
                setLoadError(true);
            })
            .finally(() => {
                if (!controller.signal.aborted) setIsLoading(false);
            });

        return () => controller.abort();
    }, [selectedChatId]);

    return children({
        messages,
        isLoading,
        loadError,
    });
}
