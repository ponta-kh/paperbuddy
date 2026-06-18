import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

import {
    type ChatCitation,
    type ChatMessage,
    getChatMessages,
} from "@/lib/chat-api";

const ANSWER_REVEAL_INTERVAL_MS = 20;
const ANSWER_REVEAL_CHUNK_SIZE = 2;

type ChatMessagesContainerProps = {
    selectedChatId?: string;
    children: (state: {
        messages: ChatMessage[];
        isLoading: boolean;
        loadError: boolean;
        onAppendUserMessage: (content: string) => string;
        onAppendAssistantMessage: (
            content: string,
            citations: ChatCitation[],
        ) => void;
        onBindCurrentChat: (chatId: string) => void;
        onMarkMessageCompleted: (messageId: string) => void;
        onMarkMessageFailed: (messageId: string) => void;
    }) => ReactNode;
};

export function ChatMessagesContainer({
    selectedChatId,
    children,
}: ChatMessagesContainerProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [loadError, setLoadError] = useState(false);
    const loadedChatIdRef = useRef<string | undefined>(undefined);
    const revealTimersRef = useRef<Set<number>>(new Set());

    useEffect(
        () => () => {
            for (const timer of revealTimersRef.current) {
                window.clearInterval(timer);
            }
        },
        [],
    );

    useEffect(() => {
        if (selectedChatId && selectedChatId === loadedChatIdRef.current) {
            return;
        }

        for (const timer of revealTimersRef.current) {
            window.clearInterval(timer);
        }
        revealTimersRef.current.clear();

        if (!selectedChatId) {
            setMessages([]);
            setLoadError(false);
            setIsLoading(false);
            loadedChatIdRef.current = undefined;
            return;
        }

        const controller = new AbortController();
        setIsLoading(true);

        getChatMessages(selectedChatId, controller.signal)
            .then((response) => {
                setMessages(response);
                setLoadError(false);
                loadedChatIdRef.current = selectedChatId;
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

    const handleAppendUserMessage = (content: string) => {
        const messageId = crypto.randomUUID();
        setMessages((currentMessages) => [
            ...currentMessages,
            {
                id: messageId,
                role: "user",
                content,
                createdAt: new Date().toISOString(),
                status: "pending",
            },
        ]);
        return messageId;
    };

    const handleAppendAssistantMessage = (
        content: string,
        citations: ChatCitation[],
    ) => {
        const messageId = crypto.randomUUID();
        const characters = Array.from(content);
        let revealedLength = 0;
        setMessages((currentMessages) => [
            ...currentMessages,
            {
                id: messageId,
                role: "assistant",
                content: "",
                citations,
                createdAt: new Date().toISOString(),
                status: "revealing",
            },
        ]);

        const timer = window.setInterval(() => {
            revealedLength = Math.min(
                revealedLength + ANSWER_REVEAL_CHUNK_SIZE,
                characters.length,
            );
            setMessages((currentMessages) =>
                currentMessages.map((message) =>
                    message.id === messageId
                        ? {
                              ...message,
                              content: characters
                                  .slice(0, revealedLength)
                                  .join(""),
                              status:
                                  revealedLength === characters.length
                                      ? "completed"
                                      : "revealing",
                          }
                        : message,
                ),
            );
            if (revealedLength === characters.length) {
                window.clearInterval(timer);
                revealTimersRef.current.delete(timer);
            }
        }, ANSWER_REVEAL_INTERVAL_MS);
        revealTimersRef.current.add(timer);
    };

    const handleBindCurrentChat = (chatId: string) => {
        loadedChatIdRef.current = chatId;
    };

    const updateMessageStatus = (
        messageId: string,
        status: "completed" | "failed",
    ) => {
        setMessages((currentMessages) =>
            currentMessages.map((message) =>
                message.id === messageId ? { ...message, status } : message,
            ),
        );
    };

    return children({
        messages,
        isLoading,
        loadError,
        onAppendUserMessage: handleAppendUserMessage,
        onAppendAssistantMessage: handleAppendAssistantMessage,
        onBindCurrentChat: handleBindCurrentChat,
        onMarkMessageCompleted: (messageId) =>
            updateMessageStatus(messageId, "completed"),
        onMarkMessageFailed: (messageId) =>
            updateMessageStatus(messageId, "failed"),
    });
}
